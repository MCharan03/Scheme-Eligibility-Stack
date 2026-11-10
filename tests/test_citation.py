from app.services.citation_service import CitationService
from app.rag.retriever import SchemeRetriever

def test_citation_extraction(retriever: SchemeRetriever):
    chunks = retriever.retrieve("PM-KISAN", target_scheme="pm_kisan", top_k=2)
    citations = CitationService.extract_citations(chunks)
    
    assert len(citations) > 0
    cite = citations[0]
    assert cite["scheme_id"] == "pm_kisan"
    assert "https://pmkisan.gov.in" in cite["official_url"]
    assert "Agriculture" in cite["department"]
    assert "Verified from official" in cite["verification_status"]

def test_citation_markdown_formatting(retriever: SchemeRetriever):
    chunks = retriever.retrieve("PM-KISAN", target_scheme="pm_kisan", top_k=1)
    citations = CitationService.extract_citations(chunks)
    md = CitationService.format_citations_markdown(citations)
    
    assert "Official Government Source Citations" in md
    assert "https://pmkisan.gov.in" in md
