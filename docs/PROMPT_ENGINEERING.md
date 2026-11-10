# Prompt Engineering Architecture

## Overview
The Government Scheme Eligibility Navigator applies formal prompt engineering methodologies to guarantee that legal and policy eligibility decisions are strictly grounded in official documents, devoid of hallucinations, and resilient to malformed outputs.

All prompts are maintained in `app/llm/prompts.py` using LangChain's `ChatPromptTemplate` and `PromptTemplate`.

---

## 1. Techniques Implemented

### A. Role / System Prompting
Every agent is instantiated with an authoritative persona that establishes operational boundaries:
- **Router Agent**: Expert Government Scheme Intent & Profile Routing Agent for Indian Citizen Services.
- **Eligibility Agent**: Authoritative Government Scheme Eligibility Evaluation Agent restricted exclusively to retrieved text.
- **Application Agent**: Official Application Guidance Agent responsible for authentic procedures and official portal URLs.
- **Explainer Agent**: Citizen Explainer Agent translating technical evaluations into accessible civic language.
- **Verification Agent**: Reflection and Fact-Checking Agent that validates grounding against source documents.

### B. Few-Shot In-Context Prompting
The `ROUTER_SYSTEM_PROMPT` uses structured few-shot demonstrations to anchor the LLM to 4 unambiguous intents:
- `DISCOVER_SCHEMES`
- `ELIGIBILITY_CHECK`
- `APPLICATION_GUIDANCE`
- `GENERAL_SCHEME_INFORMATION`

Each example demonstrates exact JSON schema output and safe summarization.

### C. Structured Output Prompting (Schema Enforcement)
Downstream evaluation requires deterministic data structures. Prompts explicitly demand JSON outputs conforming to Pydantic schemas:
- `evaluations`: List of scheme evaluations containing `status`, `conditions_met`, `conditions_failed`, and `missing_fields`.
- `application_guidance`: `official_portal_url`, `offline_option`, `steps`, and `required_documents`.

### D. Reflection & Grounding Verification
`REFLECTION_PROMPT` compares the generated draft response directly with the retrieved context:
- Verifies that all rules and benefits are directly substantiated by the retrieved text.
- Validates that no unverified citizen variables were assumed.
- Confirms that all portal links match official ministerial URLs.

---

## 2. Key Prompt Templates

### Router Prompt (`ROUTER_PROMPT`)
```python
ROUTER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", ROUTER_SYSTEM_PROMPT),
    ("human", "Citizen Query: {user_query}\nStructured Form Context: {form_context}")
])
```
*Purpose:* Decides whether vector retrieval is required and extracts profile variables without guessing.

### Eligibility Prompt (`ELIGIBILITY_PROMPT`)
```python
ELIGIBILITY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", ELIGIBILITY_SYSTEM_PROMPT),
    ("human", """Citizen Profile:
{citizen_profile}

Retrieved Official Government Scheme Documents:
{retrieved_context}

Evaluate the citizen's eligibility against the official documents.""")
])
```
*Purpose:* Implements strict condition-checking. If an essential condition depends on absent profile data, it marks the condition as `MISSING_INFO` and adds the field to `missing_fields`.

### Application Prompt (`APPLICATION_PROMPT`)
```python
APPLICATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", APPLICATION_SYSTEM_PROMPT),
    ("human", """Target Scheme / Citizen Request:
{user_query}

Retrieved Official Application Documents:
{retrieved_context}

Provide official application guidance and document checklist.""")
])
```
*Purpose:* Pulls verified steps, checklist of documents, and official `.gov.in` portal links.

### Reflection Prompt (`REFLECTION_PROMPT`)
```python
REFLECTION_PROMPT = PromptTemplate(
    input_variables=["draft_response", "retrieved_context"],
    template="""You are a Verification and Reflection Agent ensuring strict factual accuracy.
Compare the draft response against the retrieved official scheme documents..."""
)
```
*Purpose:* Ensures 100% adherence to source evidence and rejects hallucinated prerequisites.
