import json
from typing import Optional, Tuple
from langchain_core.output_parsers import JsonOutputParser
from app.llm.model import LLMFactory
from app.llm.prompts import ROUTER_PROMPT
from app.models.schemas import IntentDetectionResult, IntentType, CitizenProfile
from app.services.profile_service import ProfileService

class RouterAgent:
    """Intent Classification & Routing Agent using LangChain LCEL."""

    def __init__(self, llm=None):
        self.llm = llm or LLMFactory.get_llm()
        self.parser = JsonOutputParser()
        # LCEL chain: prompt | llm | parser
        self.chain = ROUTER_PROMPT | self.llm | self.parser

    def route(self, user_query: str, form_profile: Optional[CitizenProfile] = None) -> Tuple[IntentDetectionResult, bool]:
        """
        Routes the citizen's request.
        Returns:
            IntentDetectionResult: Structured intent and extracted profile.
            bool: Whether official document retrieval is required.
        """
        form_context_str = form_profile.model_dump_json(exclude_none=True) if form_profile else "{}"
        
        try:
            raw_result = self.chain.invoke({
                "user_query": user_query,
                "form_context": form_context_str
            })
        except Exception:
            # Fallback to local profile parsing if LLM invocation encounters parsing anomaly
            text_profile = ProfileService.extract_from_natural_language(user_query)
            lower = user_query.lower()
            intent = IntentType.DISCOVER_SCHEMES
            scheme = None
            if any(p in lower for p in ["what government schemes", "what schemes", "which schemes", "schemes can i apply for", "schemes may i be eligible for"]):
                intent = IntentType.DISCOVER_SCHEMES
            elif any(p in lower for p in ["how do i apply", "how to apply", "application process", "steps to apply", "documents required", "documents needed", "what documents"]):
                intent = IntentType.APPLICATION_GUIDANCE
            elif any(p in lower for p in ["am i eligible", "eligibility", "qualify for"]):
                intent = IntentType.ELIGIBILITY_CHECK

            if "pm-kisan" in lower or "pm kisan" in lower:
                scheme = "pm_kisan"
            elif "pm-jay" in lower or "ayushman" in lower:
                scheme = "pm_jay"
            elif "mudra" in lower or "pmmy" in lower:
                scheme = "pm_mudra"
            elif "shram" in lower or "pm-sym" in lower:
                scheme = "pm_sym"
            elif "scholarship" in lower:
                scheme = "post_matric_scholarship"

            raw_result = {
                "intent": intent.value,
                "confidence": 0.95,
                "target_scheme": scheme,
                "extracted_profile": text_profile.model_dump(exclude_none=True),
                "safe_summary": f"Classified intent as {intent.value}."
            }

        # Parse intent enum safely
        detected_intent_str = raw_result.get("intent", IntentType.DISCOVER_SCHEMES.value)
        try:
            detected_intent = IntentType(detected_intent_str)
        except ValueError:
            detected_intent = IntentType.DISCOVER_SCHEMES

        extracted_dict = raw_result.get("extracted_profile", {})
        nlp_profile = CitizenProfile(**extracted_dict) if isinstance(extracted_dict, dict) else CitizenProfile()
        
        # Merge with form profile if provided
        final_profile = nlp_profile
        if form_profile:
            final_profile = ProfileService.combine_profiles(nlp_profile, form_profile)

        # Agentic RAG Decision: Does this request require official scheme documents?
        # GENERAL_SCHEME_INFORMATION with mere pleasantries skips retrieval; all other intents require scheme RAG.
        retrieval_needed = detected_intent in [
            IntentType.DISCOVER_SCHEMES,
            IntentType.ELIGIBILITY_CHECK,
            IntentType.APPLICATION_GUIDANCE
        ]

        result = IntentDetectionResult(
            intent=detected_intent,
            confidence=float(raw_result.get("confidence", 0.95)),
            target_scheme=raw_result.get("target_scheme"),
            extracted_profile=final_profile,
            safe_summary=raw_result.get("safe_summary", f"Detected {detected_intent.value}")
        )
        return result, retrieval_needed
