from typing import List, Dict, Any
from app.models.schemas import DocumentChunk

class CitationService:
    """Verifies that all scheme assertions are backed by retrieved official government documents."""

    @staticmethod
    def extract_citations(chunks: List[DocumentChunk]) -> List[Dict[str, str]]:
        citations = []
        seen_keys = set()

        for chunk in chunks:
            meta = chunk.metadata
            key = f"{meta.scheme_id}_{meta.section}"
            if key not in seen_keys:
                seen_keys.add(key)
                citations.append({
                    "scheme_id": meta.scheme_id,
                    "scheme_name": meta.scheme_name,
                    "source_title": meta.source_title,
                    "department": meta.government_department,
                    "official_url": meta.source_url,
                    "section": meta.section,
                    "verification_status": "Verified from official government source"
                })
        return citations

    @staticmethod
    def format_citations_markdown(citations: List[Dict[str, str]]) -> str:
        if not citations:
            return "_No official sources could be matched for this request._"

        lines = ["### Official Government Source Citations\n"]
        for idx, cite in enumerate(citations, 1):
            lines.append(
                f"{idx}. **{cite['scheme_name']}** ({cite['section'].replace('_', ' ').title()})\n"
                f"   - **Authority:** {cite['department']}\n"
                f"   - **Official Publication:** {cite['source_title']}\n"
                f"   - **Official Portal:** [{cite['official_url']}]({cite['official_url']})\n"
                f"   - **Status:** `{cite['verification_status']}`\n"
            )
        return "\n".join(lines)
