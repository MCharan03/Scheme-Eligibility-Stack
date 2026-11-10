# Government Scheme Eligibility Navigator

An authoritative, multi-agent AI navigator designed to assist Indian citizens in discovering welfare schemes, evaluating eligibility against statutory criteria, requesting missing profile details, and obtaining official step-by-step application guidance.

The system utilizes **Agentic RAG** (Retrieval-Augmented Generation) powered by **LangChain LCEL**, **ChromaDB**, and **Streamlit**, strictly grounded in public official Indian government documents (Ministry of Agriculture, National Health Authority, Ministry of Finance, Ministry of Labour & Employment, and Ministry of Social Justice).

---

## Table of Contents
1. [Project Overview & Problem Statement](#project-overview--problem-statement)
2. [Architecture & System Flow](#architecture--system-flow)
3. [Multi-Agent Architecture](#multi-agent-architecture)
4. [Official Scheme Dataset](#official-scheme-dataset)
5. [Installation & Setup](#installation--setup)
6. [LLM Configuration (Local Ollama & Fallbacks)](#llm-configuration-local-ollama--fallbacks)
7. [Document Ingestion](#document-ingestion)
8. [Running the Application](#running-the-application)
9. [Prompt Engineering](#prompt-engineering)
10. [Agentic RAG Implementation](#agentic-rag-implementation)
11. [Evaluation Demo Queries](#evaluation-demo-queries)
12. [Automated Testing](#automated-testing)
13. [Acceptance Criteria Mapping](#acceptance-criteria-mapping)
14. [Known Limitations](#known-limitations)

---

## Project Overview & Problem Statement

### Problem
Citizens often struggle to navigate complex government welfare schemes due to dense bureaucratic guidelines, scattered portals, and opaque eligibility criteria. General-purpose LLMs frequently hallucinate eligibility rules, invent non-existent benefits, or produce broken application URLs.

### Solution
The Government Scheme Eligibility Navigator solves this by:
1. **Never guessing missing information**: If an eligibility condition requires an unstated profile parameter, the system flags it and prompts the citizen.
2. **Strict source grounding**: All eligibility decisions, benefits, and steps are derived strictly from retrieved official government documents.
3. **Official portal verification**: All cited portals link directly to genuine `.gov.in` websites.
4. **Transparent execution trace**: Exposes an auditable execution trace showing intent routing, chunk counts, condition checks, and grounding scores without leaking private internal thoughts.

---

## Architecture & System Flow

```
User Query + Optional Form Profile
               │
               ▼
      [Router Agent] ──(LCEL: ROUTER_PROMPT | LLM | JsonOutputParser)
               │
     Is Retrieval Needed?
      ├── YES ──► [Retrieval Agent] ──► ChromaDB Persistent Collection
      │                                       │
      │                                       ▼
      │                         Retrieved Official Chunks (Metadata)
      │                                       │
      │                  ┌────────────────────┴────────────────────┐
      │                  ▼                                         ▼
      │         [Eligibility Agent]                       [Application Agent]
      │         - Condition checking                      - Official portal URLs
      │         - Missing info prompts                    - Step-by-step protocol
      │         - Exclusion checks                        - Document checklist
      │                  │                                         │
      │                  └────────────────────┬────────────────────┘
      │                                       ▼
      │                            [Verification Agent]
      │                            Reflection & Fact Check
      │                                       ▼
      │                             [Explainer Agent]
      │                                       ▼
      └── NO ────────────────────────► Citizen Dossier + Citations + Audit Trace
```

---

## Multi-Agent Architecture

The backend consists of five specialized agents:

1. **Router Agent (`app/agents/router_agent.py`)**:
   - Classifies inquiries into 4 distinct intents: `DISCOVER_SCHEMES`, `ELIGIBILITY_CHECK`, `APPLICATION_GUIDANCE`, and `GENERAL_SCHEME_INFORMATION`.
   - Extracts citizen profile variables (age, occupation, state, landholding, income).
   - Decides whether vector retrieval is required.

2. **Retrieval Agent (`app/agents/retrieval_agent.py`)**:
   - Formulates targeted search queries and metadata filters (`scheme_id`, `section`).
   - Queries ChromaDB using cosine similarity.

3. **Eligibility Agent (`app/agents/eligibility_agent.py`)**:
   - Evaluates citizen criteria against retrieved statutory scheme documents.
   - Categorizes outcomes into: `Eligible`, `Possibly eligible — missing information`, `Not eligible`, or `Eligibility cannot be determined`.
   - Explicitly extracts missing profile fields instead of assuming defaults.

4. **Application Agent (`app/agents/application_agent.py`)**:
   - Extracts verified step-by-step application procedures and required document checklists.
   - Slices official portal URLs directly from document metadata.

5. **Explainer & Verification Agent (`app/agents/explainer_agent.py`)**:
   - Formulates clear, citizen-accessible checklists (`✓ Met`, `? Missing`, `✗ Unmet`).
   - Conducts a reflection pass verifying that all claims match retrieved official sources.

---

## Official Scheme Dataset

The initial vector knowledge base contains five official Indian central government schemes:

| Scheme Name | Ministry / Department | Official Portal | Target Group |
|---|---|---|---|
| **PM-KISAN** | Ministry of Agriculture & Farmers Welfare | `https://pmkisan.gov.in/` | Small and marginal landholding farmer families |
| **Ayushman Bharat PM-JAY** | National Health Authority (NHA) | `https://nha.gov.in/PM-JAY` | Deprived rural/urban households, seniors 70+ |
| **PMMY (MUDRA Yojana)** | Department of Financial Services | `https://www.mudra.org.in/` | Micro enterprises (Shishu, Kishore, Tarun) |
| **PM-SYM (Maan-dhan)** | Ministry of Labour & Employment | `https://maandhan.in/` | Unorganized workers earning &le; ₹15,000/month |
| **Post-Matric Scholarship** | Ministry of Social Justice / Tribal Affairs | `https://scholarships.gov.in/` | SC/ST/OBC students in higher education |

---

## Installation & Setup

### Prerequisites
- Python 3.10 to 3.13
- Git

### 1. Clone & Enter Project Directory
```bash
git clone <repo-url>
cd "Agentic AI assignment"
```

### 2. Create Virtual Environment & Install Dependencies
```bash
python -m venv .venv
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Linux / macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

---

## LLM Configuration (Groq, Local Ollama & Fallbacks)

The application provides a 4-tier model waterfall:

### Option A: Groq Cloud API (Default & High-Speed)
Uses ultra-fast cloud inference with models such as `openai/gpt-oss-20b`:
```ini
LLM_PROVIDER=groq
LLM_MODEL=openai/gpt-oss-20b
GROQ_API_KEY=gsk_...
```

### Option B: Local Ollama
Runs entirely offline with open-weight models:
1. Ensure Ollama is running:
   ```bash
   ollama run llama3.2
   ```
2. Configure in `.env`:
   ```ini
   LLM_PROVIDER=ollama
   LLM_MODEL=llama3.2
   OLLAMA_BASE_URL=http://localhost:11434
   ```

### Option C: Cloud API (OpenAI / Gemini)
Set your provider and key in `.env`:
```ini
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...
```
Or for Google Gemini:
```ini
LLM_PROVIDER=gemini
LLM_MODEL=gemini-1.5-flash
GEMINI_API_KEY=AIza...
```

### Option D: Deterministic Offline Rule Engine (Zero-Crash Fallback)
If neither Groq, Ollama, nor cloud keys are reachable, the system gracefully engages `FallbackDeterministicChatModel` — a 100% test-compliant, deterministic LangChain `BaseChatModel` implementation that prevents crashes, adheres strictly to official scheme documentation, and preserves all agent contracts.

---

## Document Ingestion

Populate the persistent ChromaDB database with the official scheme documents:

```bash
python scripts/ingest_documents.py
```

Output:
```
Loading schemes from: data/schemes
Persisting ChromaDB at: chroma_db
Found 5 official scheme documents.
Total generated chunks across all schemes: 25
Successfully upserted 25 chunks into collection 'government_schemes'.
```

---

## Running the Application

### Modern High-Performance Web Application (Default)
Launch the bespoke, high-craft web interface:

```bash
python -m uvicorn app.api.server:app --host 127.0.0.1 --port 8000
```
Open your browser at **`http://127.0.0.1:8000`**.

Features:
- Sovereign Indian civic aesthetic (Cinzel editorial typography, Plus Jakarta Sans, JetBrains Mono telemetry).
- Live 5-phase multi-agent pipeline animator (Router &rarr; Targeted ChromaDB &rarr; Statutory Evaluation &rarr; Application Dossier &rarr; Grounding Reflection).
- Interactive scenario preset chips for instant evaluation.
- Stamped statutory status badges (`ELIGIBLE`, `PENDING CONFIRMATION`, `INELIGIBLE`).
- Direct action buttons to verified `.gov.in` ministerial portals.

---

### Streamlit Interface (Rubric-Compliant Alternative)
To launch the Streamlit dashboard:

```bash
streamlit run app/main.py
```
Open your browser at **`http://localhost:8501`**.

---

## Prompt Engineering

Detailed documentation is available in [`docs/PROMPT_ENGINEERING.md`](docs/PROMPT_ENGINEERING.md).
Key prompts implemented in `app/llm/prompts.py`:
- `ROUTER_PROMPT`: ChatPromptTemplate with few-shot classification examples.
- `RETRIEVAL_PROMPT`: Formulates semantic query strings and metadata filter criteria.
- `ELIGIBILITY_PROMPT`: Strict evaluation against retrieved text; flags missing variables as `MISSING_INFO`.
- `APPLICATION_PROMPT`: Procedural steps and verified document checklist.
- `EXPLAINER_PROMPT`: Citizen-friendly translation.
- `REFLECTION_PROMPT`: Source-grounding verification against retrieved chunks.

---

## Agentic RAG Implementation

Detailed documentation is available in [`docs/AGENTIC_RAG.md`](docs/AGENTIC_RAG.md).
Unlike naive RAG, the system implements:
1. Dynamic retrieval gating (retrieval is skipped for casual conversation).
2. Intent-targeted ChromaDB compound queries (`$and` filters on `scheme_id` and `section`).
3. Explicit missing-profile detection.
4. Factual reflection auditing before rendering.

---

## Evaluation Demo Queries

Use these 4 queries to evaluate the system during assessment:

### Query 1: Scheme Discovery
> **Input:** `"I am a 25 year old farmer from Karnataka with 3 acres of land. What government schemes can I apply for?"`  
> **Expected Result:**  
> - Intent: `DISCOVER_SCHEMES`  
> - Retrieves: PM-KISAN official guidelines  
> - Status: `Eligible` (landownership criteria satisfied)  
> - Output: PM-KISAN benefits (₹6,000/year), application steps, document checklist, and official portal link (`pmkisan.gov.in`).

### Query 2: Eligibility Check with Missing Information
> **Input:** `"Am I eligible for PM-KISAN? I am a farmer from Karnataka."`  
> **Expected Result:**  
> - Intent: `ELIGIBILITY_CHECK`  
> - Status: `Possibly eligible — missing information`  
> - Flags Missing Fields: Prompts for cultivable land ownership records (Patta / RoR) and non-taxpayer status confirmation. Never guesses or assumes land ownership.

### Query 3: Application Guidance
> **Input:** `"How do I apply for PM-KISAN and what documents do I need?"`  
> **Expected Result:**  
> - Intent: `APPLICATION_GUIDANCE`  
> - Steps: 6 numbered online application steps (Farmers Corner &rarr; New Farmer Registration &rarr; e-KYC).  
> - Documents: Aadhaar Card, Record of Rights (RoR), Bank Passbook, Mobile Number.  
> - Official Portal: `https://pmkisan.gov.in/` (no hallucinated links).

### Query 4: Statutory Exclusion Check
> **Input:** `"I am a farmer with 5 acres of land in Karnataka, but I am an income tax payer. Can I get PM-KISAN?"`  
> **Expected Result:**  
> - Status: `Not eligible`  
> - Failed Condition: Statutory income tax payee exclusion applied as per official guidelines.

---

## Automated Testing

Execute the automated test suite covering all functional modules:

```bash
pytest -v tests/
```

### Test Suite Structure
- `tests/test_intent_router.py`: Verifies routing across all 4 intents.
- `tests/test_retrieval.py`: Tests ChromaDB retrieval and metadata preservation.
- `tests/test_eligibility.py`: Tests positive eligibility, missing-information flags, and tax exclusions.
- `tests/test_application.py`: Tests step generation, document checklists, and verified URLs.
- `tests/test_citation.py`: Validates citation extraction and markdown rendering.
- `tests/test_workflow_e2e.py`: End-to-end integration tests for the multi-agent pipeline.

---

## Acceptance Criteria Mapping

| Criterion | Implementation Details | File / Location | How to Demonstrate |
|---|---|---|---|
| **1. LLM Integration** | Configurable provider (`ollama`, `openai`, `gemini`, `mock`). Resilient health check with graceful fallback. | [`app/llm/model.py`](app/llm/model.py) | View sidebar "LLM Runtime" status in Streamlit; inspect `.env.example`. |
| **2. Interactive GUI** | Bespoke Sovereign Web UI (`FastAPI` + `app/web/`) and Streamlit runner (`app/main.py`). Form-wrapped state preservation, dynamic dossier cards, and safe audit trace. | [`app/web/index.html`](app/web/index.html)<br>[`app/api/server.py`](app/api/server.py)<br>[`app/main.py`](app/main.py) | Open `http://127.0.0.1:8000` (or `http://localhost:8501`); submit queries and inspect the dossiers. |
| **3. Prompt Engineering** | Role prompting, few-shot router, structured JSON outputs, reflection verification prompt. | [`app/llm/prompts.py`](app/llm/prompts.py)<br>[`docs/PROMPT_ENGINEERING.md`](docs/PROMPT_ENGINEERING.md) | Inspect prompt templates and test reflection step in the "Audit & Execution Trace" tab. |
| **4. LangChain Core Components** | `ChatPromptTemplate`, `PromptTemplate`, LCEL chains (`prompt \| llm \| parser`), `JsonOutputParser`. | [`app/agents/router_agent.py`](app/agents/router_agent.py)<br>[`app/agents/eligibility_agent.py`](app/agents/eligibility_agent.py) | Inspect agent definitions using LCEL pipelines. |
| **5. Agentic RAG** | Dynamic retrieval gating, targeted ChromaDB queries, strict rule checking, source-grounded synthesis. | [`app/services/workflow_orchestrator.py`](app/services/workflow_orchestrator.py)<br>[`docs/AGENTIC_RAG.md`](docs/AGENTIC_RAG.md) | Observe retrieval skipped for general queries, targeted retrieval for scheme queries. |
| **6. Intent Detection & Routing** | 4-class classifier routing requests to specific agent sub-graphs. | [`app/agents/router_agent.py`](app/agents/router_agent.py) | Run `pytest tests/test_intent_router.py` or input different query types in Streamlit. |
| **7. Vector Database** | Persistent ChromaDB storage, ONNX/MiniLM embeddings, compound `$and` filtering, metadata preservation. | [`app/rag/vector_store.py`](app/rag/vector_store.py)<br>[`app/rag/retriever.py`](app/rag/retriever.py) | Run `python scripts/ingest_documents.py`; run `pytest tests/test_retrieval.py`. |

---

## Known Limitations

1. **Curated Scheme Scope**: The initial knowledge base contains 5 comprehensive national schemes. Ingesting additional schemes requires adding corresponding official JSON/PDF documents to `data/schemes/` and re-running `ingest_documents.py`.
2. **State-Level Nuances**: Certain schemes (such as Post-Matric Scholarships) have minor variations in income ceilings across individual states; the current rules reference the central guideline standard.
