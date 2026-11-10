from app.rag.retriever import SchemeRetriever

def test_retrieval_returns_chunks(retriever: SchemeRetriever):
    chunks = retriever.retrieve("farmer land cultivation", top_k=3)
    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk.content
        assert chunk.metadata.scheme_name
        assert chunk.metadata.source_url
        assert chunk.metadata.government_department

def test_retrieval_metadata_preservation(retriever: SchemeRetriever):
    chunks = retriever.retrieve("PM-KISAN", target_scheme="pm_kisan", top_k=2)
    assert len(chunks) > 0
    chunk = chunks[0]
    assert chunk.metadata.scheme_id == "pm_kisan"
    assert "https://pmkisan.gov.in" in chunk.metadata.source_url
    assert "Agriculture" in chunk.metadata.government_department

def test_retrieval_section_targeting(retriever: SchemeRetriever):
    chunks = retriever.retrieve("application process steps", target_scheme="pm_kisan", target_section="application_process")
    assert len(chunks) > 0
    # Should include application process chunk
    sections = [c.metadata.section for c in chunks]
    assert "application_process" in sections
