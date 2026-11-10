from typing import List, Optional
from app.rag.vector_store import VectorStoreManager
from app.models.schemas import DocumentChunk
from app.config.settings import settings

class SchemeRetriever:
    """Retriever for targeted scheme information extraction."""

    def __init__(self, vector_store: Optional[VectorStoreManager] = None):
        self.vector_store = vector_store or VectorStoreManager()

    def retrieve(
        self,
        query: str,
        target_scheme: Optional[str] = None,
        target_section: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> List[DocumentChunk]:
        k = top_k or settings.MAX_RETRIEVAL_RESULTS
        filters = []
        if target_scheme:
            # Map common aliases to internal scheme_ids
            scheme_map = {
                "pm-kisan": "pm_kisan",
                "pmkisan": "pm_kisan",
                "pm kisan": "pm_kisan",
                "pm-jay": "pm_jay",
                "pmjay": "pm_jay",
                "ayushman": "pm_jay",
                "ayushman bharat": "pm_jay",
                "mudra": "pm_mudra",
                "pmmy": "pm_mudra",
                "pm-mudra": "pm_mudra",
                "pm-sym": "pm_sym",
                "pmsym": "pm_sym",
                "maan-dhan": "pm_sym",
                "maandhan": "pm_sym",
                "scholarship": "post_matric_scholarship",
                "post-matric": "post_matric_scholarship",
                "post matric": "post_matric_scholarship"
            }
            normalized = target_scheme.lower().strip()
            resolved_id = scheme_map.get(normalized, normalized)
            filters.append({"scheme_id": resolved_id})

        if target_section:
            filters.append({"section": target_section})

        if len(filters) == 1:
            filter_arg = filters[0]
        elif len(filters) > 1:
            filter_arg = {"$and": filters}
        else:
            filter_arg = None
        
        # If filtering produces 0 results (e.g., target_scheme was slightly off), retry without filter
        chunks = self.vector_store.query(query_text=query, n_results=k, where=filter_arg)
        if not chunks and filter_arg:
            chunks = self.vector_store.query(query_text=query, n_results=k)
            
        return chunks
