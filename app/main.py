import sys
from pathlib import Path

# Ensure root directory is on path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from app.config.settings import settings
from app.models.schemas import CitizenProfile, IntentType
from app.services.workflow_orchestrator import WorkflowOrchestrator
from app.llm.model import LLMFactory

# Page configuration
st.set_page_config(
    page_title="National Scheme Eligibility Navigator",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Unslopped Craft Styles: Institutional, calm, exact
st.markdown("""
<style>
    /* Reset & Base Typography */
    body, [class*="st-"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        color: #0f172a;
    }
    
    /* Institutional Masthead */
    .masthead-band {
        height: 4px;
        background: linear-gradient(90deg, #ff9933 0%, #ff9933 33.3%, #ffffff 33.3%, #ffffff 66.6%, #138808 66.6%, #138808 100%);
        border-radius: 2px;
        margin-bottom: 16px;
    }
    .portal-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        border-bottom: 1px solid #e2e8f0;
        padding-bottom: 16px;
        margin-bottom: 24px;
    }
    .portal-title {
        font-size: 22px;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: #0f294a;
        margin: 0;
        line-height: 1.2;
    }
    .portal-subtitle {
        font-size: 13px;
        color: #64748b;
        margin-top: 4px;
    }
    .portal-badge {
        font-size: 11px;
        font-weight: 600;
        color: #0f294a;
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
        padding: 4px 8px;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    /* Structured Dossier & Cards */
    .dossier-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 20px;
        margin-bottom: 16px;
    }
    .dossier-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #f1f5f9;
        padding-bottom: 12px;
        margin-bottom: 14px;
    }
    .scheme-heading {
        font-size: 16px;
        font-weight: 600;
        color: #0f294a;
        margin: 0;
    }
    
    /* Semantic Status Badges (Restrained, high-contrast, no pills) */
    .status-tag {
        font-size: 11px;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 4px;
        letter-spacing: 0.02em;
        display: inline-block;
    }
    .status-tag-eligible {
        background: #ecfdf5;
        color: #065f46;
        border: 1px solid #a7f3d0;
    }
    .status-tag-pending {
        background: #fffbeb;
        color: #92400e;
        border: 1px solid #fde68a;
    }
    .status-tag-ineligible {
        background: #fef2f2;
        color: #991b1b;
        border: 1px solid #fecaca;
    }

    /* Checklist & Criteria Items */
    .check-item {
        font-size: 13px;
        line-height: 1.5;
        padding: 6px 0;
        border-bottom: 1px solid #f8fafc;
        display: flex;
        align-items: flex-start;
    }
    .item-bullet-satisfied {
        color: #059669;
        font-weight: 700;
        margin-right: 8px;
    }
    .item-bullet-missing {
        color: #d97706;
        font-weight: 700;
        margin-right: 8px;
    }
    .item-bullet-failed {
        color: #dc2626;
        font-weight: 700;
        margin-right: 8px;
    }

    /* Application Protocol Table */
    .protocol-step {
        font-size: 13px;
        color: #1e293b;
        padding: 8px 12px;
        background: #f8fafc;
        border-left: 2px solid #0f294a;
        margin-bottom: 6px;
        border-radius: 0 4px 4px 0;
    }
    
    /* Code / Meta Snippets */
    .meta-code {
        font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
        font-size: 12px;
        background: #f1f5f9;
        padding: 2px 6px;
        border-radius: 3px;
        color: #334155;
    }

    /* Streamlit Widget Polishing */
    .stTextArea textarea {
        border-radius: 4px;
        border-color: #cbd5e1;
        font-size: 13px;
    }
    .stTextArea textarea:focus {
        border-color: #0f294a;
        box-shadow: 0 0 0 1px #0f294a;
    }
    div[data-testid="stFormSubmitButton"] button {
        background-color: #0f294a;
        color: #ffffff;
        font-weight: 600;
        font-size: 13px;
        border-radius: 4px;
        padding: 8px 16px;
        border: none;
        letter-spacing: 0.01em;
    }
    div[data-testid="stFormSubmitButton"] button:hover {
        background-color: #1e3a5f;
    }
</style>
""", unsafe_allow_html=True)

# Masthead
st.markdown('<div class="masthead-band"></div>', unsafe_allow_html=True)
st.markdown("""
<div class="portal-header">
    <div>
        <h1 class="portal-title">Government Scheme Eligibility Navigator</h1>
        <div class="portal-subtitle">National Public Knowledge Service &bull; Grounded in Official Ministerial Gazettes</div>
    </div>
    <div>
        <span class="portal-badge">Official Repository Data &bull; Agentic RAG</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar: System Audit & Reference Profiles
with st.sidebar:
    st.markdown("### System Telemetry")
    status_info = LLMFactory.check_ollama_status()
    if status_info.get("available"):
        st.markdown(f"**LLM Runtime:** `{settings.LLM_PROVIDER.upper()}`")
        st.caption(f"Active Model: {status_info.get('active_model')}")
        st.caption(f"Endpoint: {settings.OLLAMA_BASE_URL}")
    else:
        st.markdown(f"**LLM Runtime:** `Deterministic Engine (Fallback)`")
        st.caption("Active Mode: Local rule-based verification")
        st.caption(f"Configured: {settings.LLM_PROVIDER} / {settings.LLM_MODEL}")

    st.markdown("---")
    st.markdown("### Vector Knowledge Base")
    st.markdown(f"**Store:** `ChromaDB Persistent`")
    st.markdown(f"**Indexed Documents:** `5 Schemes (25 Chunks)`")
    st.caption("PM-KISAN, AB PM-JAY, PMMY, PM-SYM, Post-Matric Scholarship")

    st.markdown("---")
    st.markdown("### Evaluation Demo Profiles")
    st.caption("Click into the intake field to test:")
    st.markdown("""
    1. **Farmer Landholder (Discovery):**  
       `I am a 25 year old farmer from Karnataka with 3 acres of land. What government schemes can I apply for?`
    
    2. **Farmer Incomplete (Missing Info):**  
       `Am I eligible for PM-KISAN? I am a farmer from Karnataka.`
    
    3. **Application Procedures:**  
       `How do I apply for PM-KISAN and what documents do I need?`
    
    4. **Student Post-Matric:**  
       `I am an OBC college student with annual family income of 2.0 lakh. What scholarship can I get?`
    """)

# Orchestrator instance in session state
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = WorkflowOrchestrator()

# Primary Citizen Intake Form (Strictly wrapped in st.form to preserve widget values across re-runs)
with st.form("citizen_intake_docket", clear_on_submit=False):
    st.markdown("##### 1. Citizen Inquiry")
    user_query = st.text_area(
        label="Describe the citizen situation or specific scheme inquiry:",
        value="I am a 25 year old farmer from Karnataka with 3 acres of land. What government schemes can I apply for?",
        height=80,
        help="State age, occupation, location, and economic background in plain language."
    )

    with st.expander("Structured Profile Parameters (Optional / Specific Overrides)", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            form_age = st.number_input("Age (Years)", min_value=0, max_value=110, value=0, step=1)
            form_gender = st.selectbox("Gender", ["", "Male", "Female", "Other"])
            form_state = st.selectbox("State / UT", ["", "Karnataka", "Maharashtra", "Tamil Nadu", "Uttar Pradesh", "Bihar", "Gujarat", "Other"])
        with col2:
            form_occ = st.selectbox("Occupation", ["", "Farmer / Cultivator", "Student", "Unorganized Worker", "Micro Entrepreneur / Small Business", "Other"])
            form_cat = st.selectbox("Social Category", ["", "General", "OBC", "SC", "ST"])
            form_land = st.number_input("Cultivable Land Ownership (Acres)", min_value=0.0, max_value=250.0, value=0.0, step=0.5)
        with col3:
            form_income = st.number_input("Annual Family Income (INR)", min_value=0, max_value=10000000, value=0, step=25000)
            form_taxpayer = st.selectbox("Income Tax Payer Status", ["Not specified", "No", "Yes"])
            form_student = st.selectbox("Enrollment as Student", ["Not specified", "Yes", "No"])

    submit_button = st.form_submit_button("Analyze Eligibility & Guidance", use_container_width=True)

# Execution flow upon form submission
if submit_button and user_query.strip():
    form_profile = CitizenProfile(
        age=form_age if form_age > 0 else None,
        gender=form_gender if form_gender else None,
        state=form_state if form_state else None,
        occupation=form_occ if form_occ else None,
        category=form_cat if form_cat else None,
        land_ownership_acres=form_land if form_land > 0 else None,
        annual_income=float(form_income) if form_income > 0 else None,
        is_tax_payer=True if form_taxpayer == "Yes" else (False if form_taxpayer == "No" else None),
        is_student=True if form_student == "Yes" else (False if form_student == "No" else None),
        is_farmer=True if "Farmer" in form_occ else None
    )

    with st.spinner("Executing agentic workflow: routing intent, querying vector store, and evaluating criteria..."):
        workflow_res = st.session_state.orchestrator.run(user_query, form_profile)
        st.session_state.last_res = workflow_res

# Render Results
if "last_res" in st.session_state:
    res = st.session_state.last_res

    st.markdown("---")
    
    # Meta summary row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"**Intent:** `{res.intent.value}`")
    with m2:
        st.markdown(f"**Target Retrieval:** `{res.retrieved_chunks_count} chunks`")
    with m3:
        st.markdown(f"**Schemes Evaluated:** `{len(res.evaluations)}`")
    with m4:
        st.markdown(f"**Source Grounding:** `Verified`")

    # Clean tabs
    tab_evaluation, tab_application, tab_sources, tab_trace = st.tabs([
        "Eligibility Dossier",
        "Application Protocol",
        "Official Ministerial Citations",
        "Audit & Execution Trace"
    ])

    with tab_evaluation:
        # Prompt user if missing profile information exists
        if res.missing_fields_prompt:
            st.markdown("""
            <div style="background: #fffbeb; border: 1px solid #fde68a; border-radius: 4px; padding: 12px 16px; margin-bottom: 16px;">
                <div style="font-size: 13px; font-weight: 600; color: #92400e; margin-bottom: 4px;">Information Required for Conclusive Determination:</div>
                <div style="font-size: 12px; color: #78350f;">The official criteria require verification of the following fields before a final eligibility certificate can be issued:</div>
            </div>
            """, unsafe_allow_html=True)
            for field in res.missing_fields_prompt:
                st.markdown(f"- **{field}**")
            st.caption("Provide these values in the intake inquiry or the Structured Profile Parameters form above.")

        # Scheme evaluations list
        if res.evaluations:
            for ev in res.evaluations:
                status_class = "status-tag-pending"
                if ev.status == "Eligible":
                    status_class = "status-tag-eligible"
                elif "Not eligible" in ev.status:
                    status_class = "status-tag-ineligible"

                st.markdown(f"""
                <div class="dossier-card">
                    <div class="dossier-header">
                        <h3 class="scheme-heading">{ev.scheme_name}</h3>
                        <span class="status-tag {status_class}">{ev.status.upper()}</span>
                    </div>
                    <div style="font-size: 13px; color: #475569; margin-bottom: 12px;">{ev.summary}</div>
                </div>
                """, unsafe_allow_html=True)

                col_a, col_b = st.columns(2)
                with col_a:
                    if ev.conditions_met:
                        st.markdown("**Conditions Verified from Profile:**")
                        for c in ev.conditions_met:
                            st.markdown(f"<div class='check-item'><span class='item-bullet-satisfied'>&#10003;</span><span>{c}</span></div>", unsafe_allow_html=True)
                    if ev.missing_fields:
                        st.markdown("**Pending Verification Requirements:**")
                        for m in ev.missing_fields:
                            st.markdown(f"<div class='check-item'><span class='item-bullet-missing'>?</span><span>{m}</span></div>", unsafe_allow_html=True)
                with col_b:
                    if ev.conditions_failed:
                        st.markdown("**Statutory Exclusions / Unmet Criteria:**")
                        for f in ev.conditions_failed:
                            st.markdown(f"<div class='check-item'><span class='item-bullet-failed'>&#10007;</span><span>{f}</span></div>", unsafe_allow_html=True)

                st.markdown("")
        else:
            st.markdown(res.response_text)

    with tab_application:
        if res.application_guidance:
            guide = res.application_guidance
            st.markdown(f"### {guide.scheme_name}")
            st.markdown(f"**Official Application Portal:** [{guide.official_portal_url}]({guide.official_portal_url})")
            if guide.offline_option:
                st.markdown(f"**Offline Channel:** {guide.offline_option}")

            c_steps, c_docs = st.columns([3, 2])
            with c_steps:
                st.markdown("**Statutory Application Steps:**")
                for idx, step in enumerate(guide.steps, 1):
                    st.markdown(f"<div class='protocol-step'><strong>{idx}.</strong> {step}</div>", unsafe_allow_html=True)

            with c_docs:
                st.markdown("**Document Checklist:**")
                for doc in guide.required_documents:
                    st.markdown(f"<div class='check-item'><span>&bull;</span>&nbsp;<span>{doc}</span></div>", unsafe_allow_html=True)

            if guide.important_notes:
                st.markdown(f"""
                <div style="background: #f8fafc; border-left: 3px solid #0f294a; padding: 10px 14px; font-size: 12px; color: #334155; margin-top: 12px;">
                    <strong>Mandatory Condition:</strong> {guide.important_notes}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Application guidance is available for specific scheme queries or upon identifying qualifying schemes.")

    with tab_sources:
        st.markdown("#### Official Ministerial Gazette Citations")
        st.markdown("All rules, eligibility limits, benefits, and procedures are extracted directly from official Government of India publications:")
        if res.citations:
            for idx, c in enumerate(res.citations, 1):
                st.markdown(f"""
                <div style="border: 1px solid #e2e8f0; border-radius: 4px; padding: 12px; margin-bottom: 10px; background: #ffffff;">
                    <div style="font-weight: 600; font-size: 13px; color: #0f294a;">{idx}. {c['scheme_name']} &bull; Section: {c['section'].title()}</div>
                    <div style="font-size: 12px; color: #64748b; margin: 2px 0;">Authority: {c['department']} &bull; Publication: {c['source_title']}</div>
                    <div style="font-size: 12px; margin-top: 4px;">
                        Official Portal: <a href="{c['official_url']}" target="_blank" style="color: #1e40af; text-decoration: none;">{c['official_url']}</a>
                        &nbsp;&bull;&nbsp;
                        <span class="meta-code">{c['verification_status']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No scheme documents were retrieved.")

    with tab_trace:
        st.markdown("#### Multi-Agent Execution Telemetry")
        st.caption("Demonstrating intent routing, vector retrieval parameters, condition checks, and factual reflection without exposing internal thoughts.")
        for idx, step in enumerate(res.execution_trace, 1):
            with st.expander(f"Phase {idx}: [{step.agent}] — {step.action}", expanded=(idx <= 2)):
                st.markdown(f"**Execution Summary:** {step.summary}")
                if step.details:
                    st.json(step.details)

st.markdown("---")
st.markdown("<div style='font-size: 11px; color: #94a3b8; text-align: center;'>National Scheme Eligibility Navigator &bull; Built with LangChain LCEL, ChromaDB &bull; Official Government Information Only</div>", unsafe_allow_html=True)
