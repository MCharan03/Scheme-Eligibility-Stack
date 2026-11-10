from typing import List, Optional
from app.rag.retriever import SchemeRetriever
from app.models.schemas import DocumentChunk, IntentType, CitizenProfile

class RetrievalAgent:
    """Agent that formulates targeted search strategies and retrieves official scheme documents."""

    def __init__(self, retriever: Optional[SchemeRetriever] = None):
        self.retriever = retriever or SchemeRetriever()

    def retrieve_context(
        self,
        query: str,
        intent: IntentType,
        target_scheme: Optional[str] = None,
        profile: Optional[CitizenProfile] = None
    ) -> List[DocumentChunk]:
        """
        Dynamically selects sections and top_k based on intent:
        - APPLICATION_GUIDANCE: Prioritizes 'application_process' and 'required_documents'
        - ELIGIBILITY_CHECK: Prioritizes 'eligibility' and 'overview'
        - DISCOVER_SCHEMES: Searches across general/eligibility overview
        """
        target_section = None
        if intent == IntentType.APPLICATION_GUIDANCE:
            target_section = None  # Retrieve both process and document checklist
        elif intent == IntentType.ELIGIBILITY_CHECK:
            target_section = None  # Retrieve overview and eligibility

        # Augment search query with profile specifics if discovering
        search_query = query
        if intent == IntentType.DISCOVER_SCHEMES and profile:
            profile_cues = []
            if profile.occupation:
                profile_cues.append(profile.occupation)
            if profile.is_farmer:
                profile_cues.append("farmer agriculture land")
            if profile.is_student:
                profile_cues.append("student scholarship education")
            if profile.annual_income:
                profile_cues.append("income assistance")
            if profile_cues:
                search_query = f"{query} {' '.join(profile_cues)}"

        chunks = self.retriever.retrieve(
            query=search_query,
            target_scheme=target_scheme,
            target_section=target_section,
            top_k=5
        )
        return chunks
