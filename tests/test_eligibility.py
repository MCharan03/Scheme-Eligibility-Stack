from app.agents.eligibility_agent import EligibilityAgent
from app.rag.retriever import SchemeRetriever
from app.models.schemas import CitizenProfile

def test_eligibility_positive_match(retriever: SchemeRetriever, farmer_profile: CitizenProfile):
    chunks = retriever.retrieve("PM-KISAN eligibility criteria", target_scheme="pm_kisan")
    agent = EligibilityAgent()
    evals = agent.evaluate(profile=farmer_profile, chunks=chunks)
    
    assert len(evals) > 0
    kisan_eval = next((e for e in evals if e.scheme_id == "pm_kisan"), None)
    assert kisan_eval is not None
    assert kisan_eval.status == "Eligible"
    assert len(kisan_eval.conditions_met) > 0

def test_eligibility_missing_information_detection(retriever: SchemeRetriever):
    # Profile of a farmer without landholding details specified
    incomplete_profile = CitizenProfile(
        age=30,
        state="Karnataka",
        occupation="Farmer",
        is_farmer=True,
        land_ownership_acres=None # MISSING
    )
    chunks = retriever.retrieve("PM-KISAN eligibility criteria", target_scheme="pm_kisan")
    agent = EligibilityAgent()
    evals = agent.evaluate(profile=incomplete_profile, chunks=chunks)
    
    kisan_eval = next((e for e in evals if e.scheme_id == "pm_kisan"), None)
    assert kisan_eval is not None
    assert "missing information" in kisan_eval.status.lower()
    assert len(kisan_eval.missing_fields) > 0
    # Must flag land ownership as missing rather than assuming it
    assert any("land" in f.lower() for f in kisan_eval.missing_fields)

def test_eligibility_exclusion_taxpayer(retriever: SchemeRetriever):
    taxpayer_farmer = CitizenProfile(
        age=35,
        state="Karnataka",
        occupation="Farmer",
        is_farmer=True,
        land_ownership_acres=5.0,
        is_tax_payer=True # EXCLUDED
    )
    chunks = retriever.retrieve("PM-KISAN eligibility criteria", target_scheme="pm_kisan")
    agent = EligibilityAgent()
    evals = agent.evaluate(profile=taxpayer_farmer, chunks=chunks)
    
    kisan_eval = next((e for e in evals if e.scheme_id == "pm_kisan"), None)
    assert kisan_eval is not None
    assert kisan_eval.status == "Not eligible"
    assert len(kisan_eval.conditions_failed) > 0
