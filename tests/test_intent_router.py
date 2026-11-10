from app.agents.router_agent import RouterAgent
from app.models.schemas import IntentType, CitizenProfile

def test_intent_discover_schemes():
    router = RouterAgent()
    query = "I am a 25 year old farmer from Karnataka with 3 acres of land. What government schemes can I apply for?"
    res, needs_rag = router.route(query)
    
    assert res.intent == IntentType.DISCOVER_SCHEMES
    assert needs_rag is True
    assert res.extracted_profile.is_farmer is True
    assert res.extracted_profile.land_ownership_acres == 3.0
    assert res.extracted_profile.age == 25

def test_intent_eligibility_check():
    router = RouterAgent()
    query = "Am I eligible for PM-KISAN? I am a farmer from Karnataka."
    res, needs_rag = router.route(query)
    
    assert res.intent == IntentType.ELIGIBILITY_CHECK
    assert res.target_scheme == "pm_kisan"
    assert needs_rag is True

def test_intent_application_guidance():
    router = RouterAgent()
    query = "How do I apply for PM-KISAN and what documents do I need?"
    res, needs_rag = router.route(query)
    
    assert res.intent == IntentType.APPLICATION_GUIDANCE
    assert res.target_scheme == "pm_kisan"
    assert needs_rag is True

def test_intent_general_information():
    router = RouterAgent()
    query = "Hello, what does this portal do?"
    res, needs_rag = router.route(query)
    # May be general or discovery, but properly handled
    assert res.intent in [IntentType.GENERAL_SCHEME_INFORMATION, IntentType.DISCOVER_SCHEMES]
