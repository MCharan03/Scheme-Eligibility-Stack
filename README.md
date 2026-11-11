# Scheme Eligibility Stack (Yojaka AI)
### National Government Scheme Eligibility Navigator & Agentic RAG System

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-17%2F17%20Passing%20(100%25)-success.svg)](tests/)
[![Orchestration](https://img.shields.io/badge/Orchestration-LangChain%20LCEL-orange.svg)](https://python.langchain.com/)
[![Primary LLM](https://img.shields.io/badge/Primary%20LLM-Groq%20Cloud%20(GPT--OSS--20B)-purple.svg)](https://groq.com/)
[![Vector Store](https://img.shields.io/badge/Vector%20Store-ChromaDB%20Persistent-red.svg)](https://www.trychroma.com/)
[![Web UI](https://img.shields.io/badge/UI-FastAPI%20Workbench%20%2B%20Streamlit-teal.svg)](app/web/)

> An authoritative, multi-agent AI system engineered to assist Indian citizens in discovering welfare entitlements, evaluating eligibility against statutory criteria, requesting missing profile attributes, and obtaining authenticated application guidance. Strictly grounded in official Government of India documentation with zero hallucinated URLs.

---

## Table of Contents
1. [Project Overview & Core Problem](#project-overview--core-problem)
2. [Key Capabilities & Innovations](#key-capabilities--innovations)
3. [Multi-Agent System Architecture](#multi-agent-system-architecture)
4. [Statutory Knowledge Base (Dataset)](#statutory-knowledge-base-dataset)
5. [Installation & Quickstart](#installation--quickstart)
6. [LLM Configuration (4-Tier Waterfall)](#llm-configuration-4-tier-waterfall)
7. [Document Ingestion Workflow](#document-ingestion-workflow)
8. [Running the Application](#running-the-application)
   - [Option 1: Modern Bespoke Web Interface (FastAPI)](#option-1-modern-bespoke-web-interface-fastapi-recommended)
   - [Option 2: Classical Streamlit Dashboard](#option-2-classical-streamlit-dashboard)
9. [REST API Documentation](#rest-api-documentation)
10. [Prompt Engineering & LCEL Chains](#prompt-engineering--lcel-chains)
11. [Agentic RAG Implementation](#agentic-rag-implementation)
12. [Evaluation Demo Scenarios](#evaluation-demo-scenarios)
13. [Automated Test Suite & Verification](#automated-test-suite--verification)
14. [Acceptance Criteria Compliance Matrix](#acceptance-criteria-compliance-matrix)
15. [Repository Structure](#repository-structure)
16. [Security & Production Readiness](#security--production-readiness)

---

## Project Overview & Core Problem

### The Challenge
Citizens across India struggle to navigate the vast array of central and state welfare programs due to:
- **Complex, fragmented eligibility guidelines**: Rules on landholding limits, family income caps, and tax exclusion clauses are scattered across departmental circulars.
- **Generic LLM Hallucinations**: Standard LLMs often fabricate non-existent benefits, invent rules, or generate dead/fake links to government portals.
- **Presumptuous defaults**: Naive conversational assistants guess missing facts (e.g., assuming a rural citizen owns land) rather than explicitly requesting the missing data.

### The Solution: Yojaka AI
The **Scheme Eligibility Stack** resolves these shortcomings through strict, deterministic multi-agent governance:
1. **Zero-Assumption Missing Information Detection**: If a statutory condition requires a profile parameter the citizen hasn't stated, the system marks the status as `Possibly eligible — missing information` and generates targeted follow-up prompts.
2. **Deterministic Source Grounding**: All eligibility decisions, benefits, and steps are extracted strictly from retrieved official scheme guidelines.
3. **Official Portal Authentication**: Application instructions only surface verified `.gov.in` and official public statutory URLs.
4. **Transparent Audit Trace**: Every request generates an auditable, step-by-step execution trace documenting intent classification, retrieval queries, condition evaluations, and grounding scores.

---

## Key Capabilities & Innovations

- **Dynamic Retrieval Gating**: Casual greetings or non-scheme conversations skip vector database retrieval completely, conserving compute and preventing irrelevant context pollution.
- **Intent-Targeted Vector Retrieval**: Rather than doing a blunt top-$k$ similarity search, the retrieval agent inspects the detected intent and injects targeted `$and` metadata filters (`scheme_id`, `section`).
- **4-Tier LLM Resilience Waterfall**:
  1. *Tier 1 (High-Speed Cloud)*: Groq Cloud Inference (`openai/gpt-oss-20b`).
  2. *Tier 2 (Local LLM)*: Ollama (`llama3.2`).
  3. *Tier 3 (Cloud Fallback)*: OpenAI (`gpt-4o-mini`) or Google Gemini (`gemini-1.5-flash`).
  4. *Tier 4 (Offline Rule Engine)*: Built-in `FallbackDeterministicChatModel` ensuring 100% uptime and offline unit test compliance.
- **Two Complete Frontends**:
  - A modern, high-craft, unslopped workbench UI built with clean semantic HTML, CSS tokens, and reactive vanilla JavaScript.
  - A rubric-compliant Streamlit interface with full form state preservation (`st.form`).

---

## Multi-Agent System Architecture

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
       │         - Statutory condition check               - Official portal URLs
       │         - Missing field detection                 - Numbered action steps
       │         - Mandatory exclusion checks              - Required document checklist
       │                  │                                         │
       │                  └────────────────────┬────────────────────┘
       │                                       ▼
       │                            [Verification Agent]
       │                            Reflection & Source Fact Check
       │                                       ▼
       │                             [Explainer Agent]
       │                            Citizen-Friendly Dossier
       │                                       ▼
       └── NO ────────────────────────► Output Dossier + Citations + Safe Audit Trace
```

### Specialized Agents

| Agent | Source File | Responsibilities |
|---|---|---|
| **Router Agent** | [`app/agents/router_agent.py`](app/agents/router_agent.py) | Classifies queries into 4 explicit intents (`DISCOVER_SCHEMES`, `ELIGIBILITY_CHECK`, `APPLICATION_GUIDANCE`, `GENERAL_SCHEME_INFORMATION`), extracts natural language profile variables, and determines retrieval necessity. |
| **Retrieval Agent** | [`app/agents/retrieval_agent.py`](app/agents/retrieval_agent.py) | Translates citizen queries into optimized search vectors; applies compound metadata filters (`scheme_id`, `section`) to fetch targeted chunks from ChromaDB. |
| **Eligibility Agent** | [`app/agents/eligibility_agent.py`](app/agents/eligibility_agent.py) | Assesses citizen profile against retrieved official rules; outputs conditions met, conditions failed, and missing information requirements. |
| **Application Agent** | [`app/agents/application_agent.py`](app/agents/application_agent.py) | Compiles verified application procedures, document checklists, and genuine public portals from document metadata. |
| **Verification & Explainer** | [`app/agents/explainer_agent.py`](app/agents/explainer_agent.py) | Generates citizen-friendly structured checklists (`✓ Met`, `? Missing`, `✗ Unmet`) and executes a reflection pass verifying grounding against retrieved chunks. |

---

## Statutory Knowledge Base (Dataset)

The knowledge base is populated with official Government of India scheme documents residing in [`data/schemes/`](data/schemes/):

| Scheme Name | Ministry / Department | Official Portal | Target Group & Benefits |
|---|---|---|---|
| **PM-KISAN** | Ministry of Agriculture & Farmers Welfare | `https://pmkisan.gov.in/` | Small and marginal landholder farmer families; ₹6,000/year DBT income support. |
| **Ayushman Bharat PM-JAY** | National Health Authority (NHA) | `https://nha.gov.in/PM-JAY` | Bottom 40% vulnerable families & seniors aged 70+; ₹5,00,000/year cashless health cover. |
| **PMMY (MUDRA Yojana)** | Department of Financial Services | `https://www.mudra.org.in/` | Micro enterprises (Shishu: up to ₹50k, Kishore: ₹50k–₹5L, Tarun: ₹5L–₹10L/₹20L). |
| **PM-SYM (Maan-dhan)** | Ministry of Labour & Employment | `https://maandhan.in/` | Unorganized workers earning &le; ₹15,000/mo; Assured ₹3,000/month pension post 60. |
| **Post-Matric Scholarship** | Ministry of Social Justice / Tribal Affairs | `https://scholarships.gov.in/` | SC/ST/OBC students in higher education; 100% compulsory fee waiver + maintenance. |

---

## Installation & Quickstart

### Prerequisites
- Python 3.10 to 3.13
- Git

### 1. Clone Repository
```bash
git clone https://github.com/MCharan03/Scheme-Eligibility-Stack.git
cd Scheme-Eligibility-Stack
```

### 2. Set Up Virtual Environment
On Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

On Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## LLM Configuration (4-Tier Waterfall)

Configure your LLM in `.env` (copy from `.env.example`):

```bash
cp .env.example .env
```

### Option A: Groq Cloud API (Default & Ultra-Fast)
Get a free API key at [console.groq.com](https://console.groq.com) and set:
```ini
LLM_PROVIDER=groq
LLM_MODEL=openai/gpt-oss-20b
GROQ_API_KEY=gsk_your_groq_api_key_here
```

### Option B: Local Ollama (Completely Offline)
1. Install and start Ollama with your chosen model:
   ```bash
   ollama run llama3.2
   ```
2. Configure `.env`:
   ```ini
   LLM_PROVIDER=ollama
   LLM_MODEL=llama3.2
   OLLAMA_BASE_URL=http://localhost:11434
   ```

### Option C: OpenAI or Google Gemini
```ini
# OpenAI
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-your_openai_key_here

# Google Gemini
LLM_PROVIDER=gemini
LLM_MODEL=gemini-1.5-flash
GEMINI_API_KEY=AIza_your_gemini_key_here
```

### Option D: Deterministic Fallback Engine (Zero API Dependency)
If no API keys are provided and Ollama is inactive, the application automatically engages `FallbackDeterministicChatModel`. This engine handles all statutory evaluation, routing, and citations with zero network overhead.

---

## Document Ingestion Workflow

To ingest the official schemes into the persistent ChromaDB collection:

```bash
python scripts/ingest_documents.py
```

Expected output:
```text
Loading schemes from: data/schemes
Persisting ChromaDB at: chroma_db
Found 5 official scheme documents.
Total generated chunks across all schemes: 25
Successfully upserted 25 chunks into collection 'government_schemes'.
```

---

## Running the Application

### Option 1: Modern Bespoke Web Interface (FastAPI) [Recommended]
Launch the FastAPI web server mounting the high-craft frontend:

```bash
python -m uvicorn app.api.server:app --host 127.0.0.1 --port 8000
```
Visit: **`http://127.0.0.1:8000`**

**Key UI Highlights:**
- **Sovereign Aesthetic:** Designed using neutral dark ramp tokens, crisp hairlines, and typography (Plus Jakarta Sans & JetBrains Mono).
- **Interactive Preset Scenarios:** 1-click test chips for farmer discovery, missing information, senior citizens, and tax exclusions.
- **Live Pipeline Animator:** Visual progress tracking through routing, retrieval, statutory evaluation, and verification stages.
- **Audit & Execution Drawer:** Safe inspection of agent trace logs, confidence metrics, and grounding verification.

---

### Option 2: Classical Streamlit Dashboard
To launch the alternative Streamlit dashboard:

```bash
streamlit run app/main.py
```
Visit: **`http://localhost:8501`**

Includes form-wrapped inputs (`st.form`) to guarantee widget state preservation on button submission.

---

## REST API Documentation

The FastAPI backend exposes the following endpoints:

### 1. `GET /api/status`
Returns service health, active LLM provider, and ChromaDB vector collection count.
```json
{
  "status": "online",
  "llm_provider": "groq",
  "llm_model": "openai/gpt-oss-20b",
  "llm_online": true,
  "vector_db": "ChromaDB Persistent",
  "indexed_chunks": 25,
  "collection_name": "government_schemes"
}
```

### 2. `GET /api/schemes`
Returns catalog of indexed government welfare schemes and official ministerial portals.

### 3. `POST /api/evaluate`
Executes the multi-agent pipeline against a natural language query with optional structured profile parameters.
**Request Body:**
```json
{
  "query": "I am a 25 year old farmer from Karnataka with 3 acres of land. What government schemes can I apply for?",
  "profile": {
    "age": 25,
    "state": "Karnataka",
    "occupation": "Farmer",
    "land_ownership_acres": 3.0,
    "is_farmer": true,
    "is_tax_payer": false
  }
}
```

---

## Prompt Engineering & LCEL Chains

Documented extensively in [`docs/PROMPT_ENGINEERING.md`](docs/PROMPT_ENGINEERING.md):
- **Role & Persona Prompting**: Strict institutional personas that prevent colloquial speculation.
- **Few-Shot In-Context Learning**: Embedded directly in routing prompts to guide edge cases.
- **Structured Output Parsing**: Strict adherence to Pydantic schemas via LangChain `JsonOutputParser`.
- **Reflection & Grounding Loop**: `REFLECTION_PROMPT` audits drafted evaluations against retrieved context before output generation.

---

## Agentic RAG Implementation

Documented extensively in [`docs/AGENTIC_RAG.md`](docs/AGENTIC_RAG.md):
- **Dynamic Retrieval Gating**: Saves compute by bypassing vector search when queries are purely conversational.
- **Targeted Section Filtering**: Employs compound `$and` filters on ChromaDB collections to isolate sections like `eligibility` or `required_documents`.
- **Missing Information Extraction**: Explicitly categorizes unfulfilled criteria as missing fields rather than fabricating answers.

---

## Evaluation Demo Scenarios

Use these standard evaluation queries to test the pipeline:

### Scenario 1: Scheme Discovery (Positive Eligibility)
> **Input:** `"I am a 25 year old farmer from Karnataka with 3 acres of land. What government schemes can I apply for?"`  
> **Expected Output:**
> - Intent: `DISCOVER_SCHEMES`
> - Status: `Eligible` for PM-KISAN.
> - Benefits: ₹6,000 / year via Direct Benefit Transfer (DBT).
> - Documents: Aadhaar Card, Record of Rights (RoR / Patta), Bank Passbook.
> - Official Portal: Verified link to `https://pmkisan.gov.in/`.

### Scenario 2: Eligibility Check with Missing Information
> **Input:** `"Am I eligible for PM-KISAN? I am a farmer from Karnataka."`  
> **Expected Output:**
> - Intent: `ELIGIBILITY_CHECK`
> - Status: `Possibly eligible — missing information`
> - Missing Fields Identified: Cultivable land ownership documentation and non-taxpayer status confirmation.

### Scenario 3: Application Guidance & Checklist
> **Input:** `"How do I apply for PM-KISAN and what documents do I need?"`  
> **Expected Output:**
> - Intent: `APPLICATION_GUIDANCE`
> - Steps: 5 numbered steps (Farmers Corner &rarr; New Farmer Registration &rarr; Aadhaar OTP &rarr; Land record upload &rarr; e-KYC).
> - Official URL: Verified link to `https://pmkisan.gov.in/`.

### Scenario 4: Statutory Exclusion Check
> **Input:** `"I am a farmer with 5 acres of land in Karnataka, but I am an income tax payer. Can I get PM-KISAN?"`  
> **Expected Output:**
> - Status: `Not eligible`
> - Failed Condition: Statutory exclusion — income tax payees are excluded from PM-KISAN under official guidelines.

---

## Automated Test Suite & Verification

The project includes 17 automated tests covering unit, retrieval, and end-to-end multi-agent flows:

```bash
pytest -v tests/
```

### Verified Test Run Output
```text
============================= test session starts =============================
platform win32 -- Python 3.13.9, pytest-8.4.2, pluggy-1.6.0
rootdir: D:\Gemini\Agentic AI assignment
collected 17 items

tests/test_application.py::test_application_guidance_extraction PASSED   [  5%]
tests/test_application.py::test_no_fabricated_urls PASSED                [ 11%]
tests/test_citation.py::test_citation_extraction PASSED                  [ 17%]
tests/test_citation.py::test_citation_markdown_formatting PASSED         [ 23%]
tests/test_eligibility.py::test_eligibility_positive_match PASSED        [ 29%]
tests/test_eligibility.py::test_eligibility_missing_information_detection PASSED [ 35%]
tests/test_eligibility.py::test_eligibility_exclusion_taxpayer PASSED    [ 41%]
tests/test_intent_router.py::test_intent_discover_schemes PASSED         [ 47%]
tests/test_intent_router.py::test_intent_eligibility_check PASSED        [ 52%]
tests/test_intent_router.py::test_intent_application_guidance PASSED     [ 58%]
tests/test_intent_router.py::test_intent_general_information PASSED      [ 64%]
tests/test_retrieval.py::test_retrieval_returns_chunks PASSED            [ 70%]
tests/test_retrieval.py::test_retrieval_metadata_preservation PASSED     [ 76%]
tests/test_retrieval.py::test_retrieval_section_targeting PASSED         [ 82%]
tests/test_workflow_e2e.py::test_workflow_e2e_discovery PASSED           [ 88%]
tests/test_workflow_e2e.py::test_workflow_e2e_eligibility_missing_info PASSED [ 94%]
tests/test_workflow_e2e.py::test_workflow_e2e_application_guidance PASSED [100%]

============================= 17 passed in 2.17s =============================
```

---

## Acceptance Criteria Compliance Matrix

| Mandatory Criterion | Implementation Details | Evidence & Source Files |
|---|---|---|
| **1. LLM Integration** | 4-tier model provider waterfall supporting Groq, Ollama, OpenAI, Gemini, and deterministic fallback. | [`app/llm/model.py`](app/llm/model.py)<br>[`.env.example`](.env.example) |
| **2. Interactive GUI** | Bespoke Sovereign Web UI (FastAPI) and Streamlit dashboard with form-wrapped submission state preservation. | [`app/web/index.html`](app/web/index.html)<br>[`app/api/server.py`](app/api/server.py)<br>[`app/main.py`](app/main.py) |
| **3. Prompt Engineering** | Role definition, few-shot routing, strict JSON schema parsing, reflection grounding. | [`app/llm/prompts.py`](app/llm/prompts.py)<br>[`docs/PROMPT_ENGINEERING.md`](docs/PROMPT_ENGINEERING.md) |
| **4. LangChain Core** | Native LangChain LCEL pipelines (`prompt \| llm \| parser`), `ChatPromptTemplate`, and `JsonOutputParser`. | [`app/agents/router_agent.py`](app/agents/router_agent.py)<br>[`app/agents/eligibility_agent.py`](app/agents/eligibility_agent.py) |
| **5. Agentic RAG** | Dynamic retrieval gating, metadata-targeted querying, missing field detection, reflection. | [`app/services/workflow_orchestrator.py`](app/services/workflow_orchestrator.py)<br>[`docs/AGENTIC_RAG.md`](docs/AGENTIC_RAG.md) |
| **6. Intent Detection & Routing** | 4-intent classifier (`DISCOVER_SCHEMES`, `ELIGIBILITY_CHECK`, `APPLICATION_GUIDANCE`, `GENERAL_SCHEME_INFORMATION`). | [`app/agents/router_agent.py`](app/agents/router_agent.py)<br>[`tests/test_intent_router.py`](tests/test_intent_router.py) |
| **7. ChromaDB Vector Store** | Persistent vector storage, ONNX MiniLM 384-dim embeddings, section-based chunking with compound `$and` filters. | [`app/rag/vector_store.py`](app/rag/vector_store.py)<br>[`scripts/ingest_documents.py`](scripts/ingest_documents.py) |

---

## Repository Structure

```text
Scheme-Eligibility-Stack/
├── app/
│   ├── agents/                   # Specialized LangChain LCEL Agents
│   │   ├── application_agent.py  # Application guidance & checklist extractor
│   │   ├── eligibility_agent.py  # Rule evaluator with missing info detection
│   │   ├── explainer_agent.py    # Citizen-friendly explainer & reflection verifier
│   │   ├── retrieval_agent.py    # Intent-aware targeted retriever
│   │   └── router_agent.py       # 4-intent routing & NLP profile parser
│   ├── api/                      # FastAPI Backend Service
│   │   └── server.py             # REST API routes & static file mount
│   ├── config/                   # Configuration Management
│   │   └── settings.py           # Pydantic BaseSettings with .env support
│   ├── llm/                      # Model Connectors & Prompts
│   │   ├── model.py              # LLMFactory & FallbackDeterministicChatModel
│   │   └── prompts.py            # Centralized LCEL prompt templates
│   ├── models/                   # Pydantic Data Contracts
│   │   └── schemas.py            # CitizenProfile, SchemeEvaluation, WorkflowResult
│   ├── rag/                      # Vector Store & Ingestion Pipeline
│   │   ├── chunker.py            # Section-based scheme chunker
│   │   ├── document_loader.py    # Scheme JSON loader
│   │   ├── embeddings.py         # Embedding function wrapper
│   │   ├── retriever.py          # SchemeRetriever with compound filters
│   │   └── vector_store.py       # Persistent ChromaDB client manager
│   ├── services/                 # Workflow Orchestration
│   │   ├── citation_service.py   # Source citation extraction & formatting
│   │   ├── profile_service.py    # Natural language profile extractor & merger
│   │   └── workflow_orchestrator.py # Multi-agent execution pipeline
│   ├── utils/                    # Observability & Trace
│   │   └── logger.py             # ExecutionTracer (safe audit trail)
│   ├── web/                      # High-Craft Web UI (FastAPI Static)
│   │   ├── css/style.css         # Unslopped neutral design system tokens
│   │   ├── js/app.js             # Reactive workbench application logic
│   │   └── index.html            # Civic workbench layout
│   └── main.py                   # Alternative Streamlit Dashboard
├── data/
│   └── schemes/                  # Official Government Scheme Documents (JSON)
│       ├── pm_jay.json           # Ayushman Bharat PM-JAY
│       ├── pm_kisan.json         # PM-KISAN
│       ├── pm_mudra.json         # PMMY MUDRA Loans
│       ├── pm_sym.json           # PM Shram Yogi Maan-dhan
│       └── post_matric_scholarship.json # SC/ST/OBC Post-Matric Scholarship
├── docs/                         # Assignment Documentation
│   ├── AGENTIC_RAG.md            # Detailed Agentic RAG architecture & design
│   └── PROMPT_ENGINEERING.md     # Detailed prompt engineering documentation
├── scripts/
│   └── ingest_documents.py       # Batch document ingestion into ChromaDB
├── tests/                        # 17 Automated Test Cases
│   ├── conftest.py               # Test fixtures & mock isolation
│   ├── test_application.py       # Application guidance tests
│   ├── test_citation.py          # Citation & URL verification tests
│   ├── test_eligibility.py       # Eligibility, missing info, exclusion tests
│   ├── test_intent_router.py     # 4-intent routing tests
│   ├── test_retrieval.py         # Vector store retrieval & filter tests
│   └── test_workflow_e2e.py      # Multi-agent end-to-end integration tests
├── .env.example                  # Environment configuration template
├── .gitignore                    # Secrets, caches, and ChromaDB binary exclusions
├── requirements.txt              # Production Python package requirements
└── README.md                     # Comprehensive project documentation
```

---

## Security & Production Readiness

- **Zero Credential Leaks**: `.gitignore` strictly protects `.env`, local database binaries (`chroma_db/`), and cache directories from being committed.
- **No Hallucinated URLs**: Every government portal URL surfaced by the UI is validated against official scheme documents and whitelist-checked.
- **Privacy-Safe Audit Trail**: The `ExecutionTracer` records agent actions, condition checks, and grounding scores while preserving citizen data confidentiality and suppressing private chain-of-thought traces.

---

### Author & Academic Attribution
Developed for **Agentic AI Assignment 3** (Multi-Agent RAG & Welfare Eligibility Navigator).  
Repository: [https://github.com/MCharan03/Scheme-Eligibility-Stack.git](https://github.com/MCharan03/Scheme-Eligibility-Stack.git)
