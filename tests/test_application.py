from app.agents.application_agent import ApplicationAgent
from app.rag.retriever import SchemeRetriever

def test_application_guidance_extraction(retriever: SchemeRetriever):
    chunks = retriever.retrieve("PM-KISAN application steps documents", target_scheme="pm_kisan")
    agent = ApplicationAgent()
    guidance = agent.guide("How do I apply for PM-KISAN?", chunks)
    
    assert guidance is not None
    assert guidance.official_portal_url == "https://pmkisan.gov.in/"
    assert len(guidance.steps) >= 3
    assert len(guidance.required_documents) >= 3
    assert any("aadhaar" in d.lower() for d in guidance.required_documents)

def test_no_fabricated_urls(retriever: SchemeRetriever):
    chunks = retriever.retrieve("PM-KISAN", target_scheme="pm_kisan")
    agent = ApplicationAgent()
    guidance = agent.guide("How to apply", chunks)
    
    assert guidance is not None
    # Must use official gov domain
    assert ".gov.in" in guidance.official_portal_url
