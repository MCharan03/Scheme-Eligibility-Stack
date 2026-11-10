import sys
import os
from pathlib import Path
import pytest

# Force deterministic fallback model during tests
os.environ["LLM_PROVIDER"] = "mock"

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.rag.vector_store import VectorStoreManager
from app.rag.retriever import SchemeRetriever
from app.services.workflow_orchestrator import WorkflowOrchestrator
from app.models.schemas import CitizenProfile

@pytest.fixture(scope="session")
def vector_store():
    vs = VectorStoreManager()
    return vs

@pytest.fixture(scope="session")
def retriever(vector_store):
    return SchemeRetriever(vector_store=vector_store)

@pytest.fixture(scope="session")
def orchestrator():
    return WorkflowOrchestrator()

@pytest.fixture
def farmer_profile():
    return CitizenProfile(
        age=25,
        state="Karnataka",
        occupation="Farmer",
        land_ownership_acres=3.0,
        is_farmer=True,
        is_tax_payer=False
    )

@pytest.fixture
def student_profile():
    return CitizenProfile(
        age=20,
        state="Karnataka",
        occupation="Student",
        annual_income=200000.0,
        category="OBC",
        is_student=True
    )
