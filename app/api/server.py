import sys
from pathlib import Path

# Ensure root directory is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.config.settings import settings
from app.models.schemas import CitizenProfile, WorkflowResult
from app.services.workflow_orchestrator import WorkflowOrchestrator
from app.llm.model import LLMFactory
from app.rag.vector_store import VectorStoreManager

app = FastAPI(
    title="National Scheme Eligibility Navigator API",
    description="High-performance Agentic RAG API for Indian Government Scheme Eligibility",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize singletons
orchestrator = WorkflowOrchestrator()
vector_store = VectorStoreManager()

class QueryRequest(BaseModel):
    query: str
    profile: Optional[CitizenProfile] = None

@app.get("/api/status")
async def get_system_status() -> Dict[str, Any]:
    provider = settings.LLM_PROVIDER.lower().strip()
    if provider == "groq":
        provider_status = LLMFactory.check_groq_status()
    else:
        provider_status = LLMFactory.check_ollama_status()
    db_count = vector_store.count()
    return {
        "status": "online",
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
        "llm_online": provider_status.get("available", False),
        "vector_db": "ChromaDB Persistent",
        "indexed_chunks": db_count,
        "collection_name": settings.CHROMA_COLLECTION_NAME
    }

@app.get("/api/schemes")
async def get_indexed_schemes():
    return [
        {
            "id": "pm_kisan",
            "name": "PM-KISAN",
            "full_name": "Pradhan Mantri Kisan Samman Nidhi",
            "ministry": "Ministry of Agriculture & Farmers Welfare",
            "portal": "https://pmkisan.gov.in/",
            "target": "Small and marginal landholding farmer families",
            "benefit": "₹6,000 / year via DBT"
        },
        {
            "id": "pm_jay",
            "name": "Ayushman Bharat PM-JAY",
            "full_name": "Pradhan Mantri Jan Arogya Yojana",
            "ministry": "National Health Authority",
            "portal": "https://nha.gov.in/PM-JAY",
            "target": "Deprived rural/urban families and seniors 70+",
            "benefit": "₹5,00,000 / year cashless health cover"
        },
        {
            "id": "pm_mudra",
            "name": "PMMY (MUDRA)",
            "full_name": "Pradhan Mantri MUDRA Yojana",
            "ministry": "Department of Financial Services",
            "portal": "https://www.mudra.org.in/",
            "target": "Non-farm micro and small enterprises",
            "benefit": "Collateral-free loans up to ₹10-20 Lakh"
        },
        {
            "id": "pm_sym",
            "name": "PM-SYM",
            "full_name": "PM Shram Yogi Maan-dhan",
            "ministry": "Ministry of Labour & Employment",
            "portal": "https://maandhan.in/",
            "target": "Unorganized workers aged 18-40 earning ≤ ₹15,000/mo",
            "benefit": "Assured ₹3,000 / month pension at age 60"
        },
        {
            "id": "post_matric_scholarship",
            "name": "Post-Matric Scholarship",
            "full_name": "Centrally Sponsored Scheme for SC/ST/OBC Students",
            "ministry": "Ministry of Social Justice & Empowerment",
            "portal": "https://scholarships.gov.in/",
            "target": "SC/ST/OBC students in higher education",
            "benefit": "100% fee reimbursement + maintenance allowance"
        }
    ]

@app.post("/api/evaluate", response_model=WorkflowResult)
async def evaluate_eligibility(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")
    try:
        result = orchestrator.run(user_query=req.query, form_profile=req.profile)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution error: {str(e)}")

# Mount static web directory
WEB_DIR = ROOT_DIR / "app" / "web"
app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

@app.get("/")
async def serve_index():
    index_file = WEB_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Frontend file not found.")
    return FileResponse(str(index_file))

def start_server(host: str = "127.0.0.1", port: int = 8000):
    import uvicorn
    uvicorn.run("app.api.server:app", host=host, port=port, reload=False)

if __name__ == "__main__":
    start_server()
