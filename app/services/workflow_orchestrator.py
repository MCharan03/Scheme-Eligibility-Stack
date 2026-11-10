from typing import Optional, List
from app.agents.router_agent import RouterAgent
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.eligibility_agent import EligibilityAgent
from app.agents.application_agent import ApplicationAgent
from app.agents.explainer_agent import ExplainerAgent
from app.services.citation_service import CitationService
from app.utils.logger import ExecutionTracer
from app.models.schemas import (
    CitizenProfile,
    WorkflowResult,
    IntentType,
    SchemeEvaluation,
    ApplicationGuidance
)

class WorkflowOrchestrator:
    """
    Multi-Agent Orchestrator executing the complete Agentic RAG pipeline.
    Maintains a safe, transparent execution trace without revealing internal thought.
    """

    def __init__(self):
        self.router = RouterAgent()
        self.retriever_agent = RetrievalAgent()
        self.eligibility_agent = EligibilityAgent()
        self.application_agent = ApplicationAgent()
        self.explainer_agent = ExplainerAgent()
        self.citation_service = CitationService()

    def run(self, user_query: str, form_profile: Optional[CitizenProfile] = None) -> WorkflowResult:
        tracer = ExecutionTracer()

        # Step 1: Intent Routing & Profile Extraction
        intent_res, retrieval_needed = self.router.route(user_query, form_profile)
        tracer.record_step(
            agent="RouterAgent",
            action="Intent Classification & Routing",
            summary=f"Detected Intent: {intent_res.intent.value} (Confidence: {intent_res.confidence:.2f})",
            details={
                "intent": intent_res.intent.value,
                "target_scheme": intent_res.target_scheme,
                "extracted_profile": intent_res.extracted_profile.model_dump(exclude_none=True)
            }
        )

        retrieved_chunks = []
        if retrieval_needed:
            # Step 2: Retrieval Agent (Vector Search in ChromaDB)
            retrieved_chunks = self.retriever_agent.retrieve_context(
                query=user_query,
                intent=intent_res.intent,
                target_scheme=intent_res.target_scheme,
                profile=intent_res.extracted_profile
            )
            tracer.record_step(
                agent="RetrievalAgent",
                action="ChromaDB Targeted Retrieval",
                summary=f"Retrieved {len(retrieved_chunks)} official document chunks",
                details={
                    "chunks_retrieved": len(retrieved_chunks),
                    "chunk_ids": [c.id for c in retrieved_chunks],
                    "sources": list({c.metadata.source_title for c in retrieved_chunks})
                }
            )
        else:
            tracer.record_step(
                agent="RetrievalAgent",
                action="Retrieval Skipped",
                summary="General conversational intent detected; ChromaDB retrieval bypassed.",
                details={"retrieval_needed": False}
            )

        evaluations: List[SchemeEvaluation] = []
        application_guidance: Optional[ApplicationGuidance] = None
        missing_fields: List[str] = []

        # Step 3: Eligibility Evaluation
        if intent_res.intent in [IntentType.DISCOVER_SCHEMES, IntentType.ELIGIBILITY_CHECK]:
            evaluations = self.eligibility_agent.evaluate(
                profile=intent_res.extracted_profile,
                chunks=retrieved_chunks
            )
            for ev in evaluations:
                missing_fields.extend(ev.missing_fields)
            
            tracer.record_step(
                agent="EligibilityAgent",
                action="Official Rule Evaluation",
                summary=f"Evaluated {len(evaluations)} schemes against citizen profile",
                details={
                    "schemes_evaluated": [ev.scheme_name for ev in evaluations],
                    "statuses": [ev.status for ev in evaluations],
                    "missing_fields": missing_fields
                }
            )

            # If eligible or specifically checking a scheme, fetch application guidance
            has_eligible = any("Eligible" in ev.status for ev in evaluations)
            if has_eligible or intent_res.target_scheme:
                application_guidance = self.application_agent.guide(user_query, retrieved_chunks)
                if application_guidance:
                    tracer.record_step(
                        agent="ApplicationAgent",
                        action="Application Guidance Formulation",
                        summary=f"Generated steps and checklist for {application_guidance.scheme_name}",
                        details={
                            "official_portal": application_guidance.official_portal_url,
                            "document_count": len(application_guidance.required_documents)
                        }
                    )

        # Step 4: Direct Application Guidance Intent
        elif intent_res.intent == IntentType.APPLICATION_GUIDANCE:
            application_guidance = self.application_agent.guide(user_query, retrieved_chunks)
            if application_guidance:
                tracer.record_step(
                    agent="ApplicationAgent",
                    action="Application Guidance Formulation",
                    summary=f"Generated steps and checklist for {application_guidance.scheme_name}",
                    details={
                        "official_portal": application_guidance.official_portal_url,
                        "document_count": len(application_guidance.required_documents)
                    }
                )

        # Step 5: Citation Service
        citations = self.citation_service.extract_citations(retrieved_chunks)

        # Step 6: Explainer Agent
        citizen_text = self.explainer_agent.explain(
            intent=intent_res.intent,
            profile=intent_res.extracted_profile,
            evaluations=evaluations,
            application_guidance=application_guidance,
            citations=citations
        )

        # Step 7: Reflection & Grounding Verification
        context_str = "\n".join([c.content for c in retrieved_chunks])
        verification_result = self.explainer_agent.verify_grounding(citizen_text, context_str)
        tracer.record_step(
            agent="VerificationAgent",
            action="Fact & Grounding Reflection",
            summary=f"Grounding verified: {verification_result.get('verified', True)}",
            details={
                "grounding_score": verification_result.get("grounding_score", 1.0),
                "notes": verification_result.get("verification_notes", "Verified")
            }
        )

        return WorkflowResult(
            query=user_query,
            intent=intent_res.intent,
            citizen_profile=intent_res.extracted_profile,
            retrieval_needed=retrieval_needed,
            retrieved_chunks_count=len(retrieved_chunks),
            evaluations=evaluations,
            application_guidance=application_guidance,
            missing_fields_prompt=list(set(missing_fields)),
            response_text=citizen_text,
            citations=citations,
            execution_trace=tracer.get_trace()
        )
