# Agentic RAG Architecture

## Overview
Traditional (naive) RAG follows an inflexible, linear pipeline:
```
User Query ──► Similarity Search ──► LLM Generation
```
In high-stakes public civic services, naive RAG fails because:
1. It retrieves documents indiscriminately, even for casual pleasantries or out-of-scope queries.
2. It assumes missing citizen information or hallucinates qualifications to fill context gaps.
3. It conflates application steps with eligibility rules, returning generic advice.
4. It fails to cite authoritative government sources for each distinct eligibility condition.

The **Government Scheme Eligibility Navigator** implements true **Agentic RAG**, where the system acts as an orchestrated team of specialized agents with a dynamic decision graph.

---

## Architecture Flow

```
                      Citizen Request (Text + Structured Form)
                                         │
                                         ▼
                               [Router Agent]
                          Intent & Entity Detection
                                         │
                    ┌────────────────────┴────────────────────┐
                    │                                         │
    Requires Official Scheme Data?                   Casual Inquiry?
                    │                                         │
                   YES                                       NO
                    │                                         │
                    ▼                                         ▼
            [Retrieval Agent]                          Direct Explainer
         Query Formulation & Filtering                        │
                    │                                         ▼
                    ▼                                 Citizen Response
            Persistent ChromaDB
      (Official Scheme Guidelines)
                    │
                    ▼
          Retrieved Official Chunks
       (Metadata: Ministry, URLs, Rules)
                    │
       ┌────────────┴────────────┐
       ▼                         ▼
[Eligibility Agent]       [Application Agent]
- Rule Satisfaction        - Step-by-Step Procedures
- Missing Info Prompts     - Mandatory Documents
- Exclusion Checking       - Official Portals
       │                         │
       └────────────┬────────────┘
                    │
                    ▼
           [Verification Agent]
      Source Grounding & Reflection
                    │
                    ▼
           [Explainer Agent]
      Citizen-Facing Dossier & Citations
```

---

## Agentic Decision Capabilities

### 1. Dynamic Retrieval Decision
The Router Agent analyzes citizen inquiries and determines if vector retrieval is necessary:
- Inquiries with intent `DISCOVER_SCHEMES`, `ELIGIBILITY_CHECK`, or `APPLICATION_GUIDANCE` route to the Retrieval Agent.
- General conversational requests or pleasantries bypass the vector database.

### 2. Targeted Section Retrieval & Filtering
Rather than performing a naive dump of top-k vectors, the Retrieval Agent:
- Targets specific scheme IDs (`pm_kisan`, `pm_jay`, `pm_mudra`, `pm_sym`, `post_matric_scholarship`) when named.
- Targets specific sections (e.g. `application_process` and `required_documents` for `APPLICATION_GUIDANCE`).
- Filters using ChromaDB compound `$and` filters.

### 3. Strict Rule Verification & Missing Information Detection
The Eligibility Agent never guesses or invents criteria:
- Every condition is verified against citizen parameters.
- If a required criterion (e.g., cultivable land records or family income certificate) has not been stated by the citizen, the agent sets the status to **"Possibly eligible — missing information"**, explicitly lists the missing attributes, and prompts the citizen to provide them.

### 4. Source Citation & Grounding
Every claim is verified against official metadata (`source_title`, `department`, `source_url`, `section`) and audited through a reflection step before rendering to the citizen.
