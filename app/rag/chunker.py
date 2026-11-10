from typing import List, Dict, Any
from app.models.schemas import DocumentChunk, DocumentChunkMetadata

class SchemeChunker:
    """Chunks official government scheme data into section-oriented, semantically cohesive chunks."""

    @staticmethod
    def chunk_scheme(scheme: Dict[str, Any]) -> List[DocumentChunk]:
        chunks: List[DocumentChunk] = []
        scheme_id = scheme.get("scheme_id", "unknown")
        scheme_name = scheme.get("scheme_name", "Unknown Scheme")
        source_title = scheme.get("source_title", "Official Government Portal")
        source_url = scheme.get("source_url", "")
        department = scheme.get("department", scheme.get("ministry", "Government of India"))

        base_meta = {
            "scheme_id": scheme_id,
            "scheme_name": scheme_name,
            "source_title": source_title,
            "source_url": source_url,
            "government_department": department,
            "document_type": "official_scheme_document"
        }

        # 1. Overview Chunk
        overview_text = (
            f"Official Scheme: {scheme_name} ({scheme.get('short_name', '')})\n"
            f"Ministry / Department: {scheme.get('ministry', '')} | {department}\n"
            f"Official Portal: {source_url}\n"
            f"Target Beneficiaries: {scheme.get('target_beneficiaries', '')}\n"
        )
        chunks.append(DocumentChunk(
            id=f"{scheme_id}_overview",
            content=overview_text,
            metadata=DocumentChunkMetadata(**base_meta, section="overview")
        ))

        # 2. Eligibility Criteria Chunk
        elig_data = scheme.get("eligibility_criteria", {})
        elig_lines = [f"Eligibility Rules and Criteria for {scheme_name}:"]
        for k, v in elig_data.items():
            if isinstance(v, list):
                elig_lines.append(f"- {k.replace('_', ' ').title()}:")
                for item in v:
                    elig_lines.append(f"  * {item}")
            else:
                elig_lines.append(f"- {k.replace('_', ' ').title()}: {v}")

        chunks.append(DocumentChunk(
            id=f"{scheme_id}_eligibility",
            content="\n".join(elig_lines),
            metadata=DocumentChunkMetadata(**base_meta, section="eligibility")
        ))

        # 3. Benefits Chunk
        ben_data = scheme.get("benefits", {})
        ben_lines = [f"Official Benefits and Financial Assistance under {scheme_name}:"]
        for k, v in ben_data.items():
            ben_lines.append(f"- {k.replace('_', ' ').title()}: {v}")

        chunks.append(DocumentChunk(
            id=f"{scheme_id}_benefits",
            content="\n".join(ben_lines),
            metadata=DocumentChunkMetadata(**base_meta, section="benefits")
        ))

        # 4. Application Process Chunk
        app_data = scheme.get("application_process", {})
        app_lines = [f"Official Step-by-Step Application Procedures for {scheme_name}:"]
        if "online_portal" in app_data:
            app_lines.append(f"- Official Online Portal: {app_data['online_portal']}")
        if "online_steps" in app_data:
            app_lines.append("- Online Application Steps:")
            for idx, step in enumerate(app_data["online_steps"], 1):
                app_lines.append(f"  {idx}. {step}")
        if "offline_option" in app_data:
            app_lines.append(f"- Offline Application Option: {app_data['offline_option']}")

        chunks.append(DocumentChunk(
            id=f"{scheme_id}_application_process",
            content="\n".join(app_lines),
            metadata=DocumentChunkMetadata(**base_meta, section="application_process")
        ))

        # 5. Required Documents Chunk
        docs_data = scheme.get("required_documents", [])
        doc_lines = [f"Official Checklist of Required Documents for {scheme_name}:"]
        for doc in docs_data:
            doc_lines.append(f"- {doc}")

        chunks.append(DocumentChunk(
            id=f"{scheme_id}_required_documents",
            content="\n".join(doc_lines),
            metadata=DocumentChunkMetadata(**base_meta, section="required_documents")
        ))

        return chunks
