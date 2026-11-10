from app.services.workflow_orchestrator import WorkflowOrchestrator
from app.models.schemas import IntentType

def test_workflow_e2e_discovery(orchestrator: WorkflowOrchestrator):
    query = "I am a 25 year old farmer from Karnataka with 3 acres of land. What government schemes can I apply for?"
    result = orchestrator.run(query)

    assert result.intent == IntentType.DISCOVER_SCHEMES
    assert result.retrieval_needed is True
    assert result.retrieved_chunks_count > 0
    assert len(result.evaluations) > 0
    assert len(result.citations) > 0
    assert len(result.execution_trace) >= 4
    
    # Check trace contents (safe trace, no internal thoughts)
    agents_involved = [t.agent for t in result.execution_trace]
    assert "RouterAgent" in agents_involved
    assert "RetrievalAgent" in agents_involved
    assert "EligibilityAgent" in agents_involved

def test_workflow_e2e_eligibility_missing_info(orchestrator: WorkflowOrchestrator):
    query = "Am I eligible for PM-KISAN? I am a farmer from Karnataka."
    result = orchestrator.run(query)

    assert result.intent == IntentType.ELIGIBILITY_CHECK
    assert result.retrieval_needed is True
    assert len(result.evaluations) > 0
    pm_eval = result.evaluations[0]
    assert "missing information" in pm_eval.status.lower()
    assert len(result.missing_fields_prompt) > 0

def test_workflow_e2e_application_guidance(orchestrator: WorkflowOrchestrator):
    query = "How do I apply for PM-KISAN and what documents do I need?"
    result = orchestrator.run(query)

    assert result.intent == IntentType.APPLICATION_GUIDANCE
    assert result.application_guidance is not None
    assert "pmkisan.gov.in" in result.application_guidance.official_portal_url
    assert len(result.application_guidance.required_documents) > 0
