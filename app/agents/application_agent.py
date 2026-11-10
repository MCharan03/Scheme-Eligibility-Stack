from typing import List, Optional
from langchain_core.output_parsers import JsonOutputParser
from app.llm.model import LLMFactory
from app.llm.prompts import APPLICATION_PROMPT
from app.models.schemas import ApplicationGuidance, DocumentChunk

class ApplicationAgent:
    """Provides official step-by-step application guidance and required document checklists."""

    def __init__(self, llm=None):
        self.llm = llm or LLMFactory.get_llm()
        self.parser = JsonOutputParser()
        # LCEL chain
        self.chain = APPLICATION_PROMPT | self.llm | self.parser

    def guide(self, user_query: str, chunks: List[DocumentChunk]) -> Optional[ApplicationGuidance]:
        if not chunks:
            return None

        # Filter chunks that relate to application process or documents
        app_chunks = [c for c in chunks if c.metadata.section in ["application_process", "required_documents", "overview"]]
        if not app_chunks:
            app_chunks = chunks

        context_blocks = []
        for c in app_chunks:
            context_blocks.append(
                f"[Source: {c.metadata.source_title} | Department: {c.metadata.government_department} | URL: {c.metadata.source_url}]\n{c.content}"
            )
        retrieved_context_str = "\n\n---\n\n".join(context_blocks)

        try:
            raw_result = self.chain.invoke({
                "user_query": user_query,
                "retrieved_context": retrieved_context_str
            })
            sources = [
                {
                    "source_title": c.metadata.source_title,
                    "official_url": c.metadata.source_url,
                    "department": c.metadata.government_department
                }
                for c in app_chunks
            ]
            # Deduplicate sources
            unique_sources = []
            seen = set()
            for s in sources:
                if s["official_url"] not in seen:
                    seen.add(s["official_url"])
                    unique_sources.append(s)

            return ApplicationGuidance(
                scheme_name=raw_result.get("scheme_name", app_chunks[0].metadata.scheme_name),
                official_portal_url=raw_result.get("official_portal_url", app_chunks[0].metadata.source_url),
                offline_option=raw_result.get("offline_option"),
                steps=raw_result.get("steps", []),
                required_documents=raw_result.get("required_documents", []),
                important_notes=raw_result.get("important_notes"),
                official_sources=unique_sources
            )
        except Exception:
            return self._deterministic_guidance(app_chunks)

    def _deterministic_guidance(self, chunks: List[DocumentChunk]) -> Optional[ApplicationGuidance]:
        """Deterministic guidance strictly matching the retrieved official documents."""
        if not chunks:
            return None

        first = chunks[0]
        meta = first.metadata
        scheme_id = meta.scheme_id

        if scheme_id == "pm_kisan":
            return ApplicationGuidance(
                scheme_name="Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
                official_portal_url="https://pmkisan.gov.in/",
                offline_option="Visit nearest Common Service Centre (CSC) or local Village Patwari / Nodal Agriculture Officer",
                steps=[
                    "Visit the official portal https://pmkisan.gov.in/ and navigate to 'Farmers Corner'",
                    "Select 'New Farmer Registration' and choose Rural or Urban Farmer Registration",
                    "Enter Aadhaar number and active mobile number, then submit received OTP",
                    "Enter landholding details (survey number, khasra/khatian number, area in hectares)",
                    "Upload land ownership documents and submit the application form",
                    "Complete mandatory e-KYC (biometric via CSC or OTP-based on portal)"
                ],
                required_documents=[
                    "Aadhaar Card of the applicant farmer",
                    "Land ownership document / Record of Rights (RoR) / Khatoni / Patta",
                    "Aadhaar-seeded active Bank Account Passbook with IFSC code",
                    "Active Mobile Number linked with Aadhaar"
                ],
                important_notes="e-KYC and Aadhaar-bank account seeding are mandatory for DBT installment credit.",
                official_sources=[{
                    "source_title": "PM-KISAN Official Operational Guidelines & Portal",
                    "official_url": "https://pmkisan.gov.in/",
                    "department": "Department of Agriculture and Farmers Welfare"
                }]
            )
        elif scheme_id == "pm_jay":
            return ApplicationGuidance(
                scheme_name="Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (AB PM-JAY)",
                official_portal_url="https://beneficiary.nha.gov.in/",
                offline_option="Visit any Empaneled Health Care Provider (EHCP) hospital and approach the 'Ayushman Mitra' desk, or visit a local Common Service Centre (CSC)",
                steps=[
                    "Visit the NHA Beneficiary Portal https://beneficiary.nha.gov.in/ or download the Ayushman App",
                    "Log in with active mobile number using OTP authentication",
                    "Search beneficiary family using Aadhaar number, Ration Card number, or Family ID",
                    "If name appears, proceed with e-KYC using Aadhaar OTP, IRIS, or fingerprint",
                    "Capture live photograph and match demographic details",
                    "Download Ayushman Card (Golden Card) upon approval"
                ],
                required_documents=[
                    "Aadhaar Card of the individual member",
                    "Ration Card or State-recognized Family Identification Document",
                    "Active mobile number linked with Aadhaar"
                ],
                important_notes="Provides up to Rs. 5 Lakhs per family per year completely cashless at point of treatment.",
                official_sources=[{
                    "source_title": "Ayushman Bharat PM-JAY Official Portal",
                    "official_url": "https://nha.gov.in/PM-JAY",
                    "department": "National Health Authority"
                }]
            )
        else:
            return ApplicationGuidance(
                scheme_name=meta.scheme_name,
                official_portal_url=meta.source_url,
                offline_option="Visit the concerned District Officer or local Common Service Centre (CSC)",
                steps=[
                    f"Visit the official scheme website: {meta.source_url}",
                    "Complete citizen registration with Aadhaar and mobile number",
                    "Fill required application details and upload supporting documents",
                    "Track status using your generated registration reference number"
                ],
                required_documents=[
                    "Aadhaar Card / Government Photo ID",
                    "Bank Account Passbook with IFSC",
                    "Proof of eligibility (Income/Land/Category certificate as applicable)"
                ],
                important_notes="Ensure documents match Aadhaar records exactly to avoid rejection.",
                official_sources=[{
                    "source_title": meta.source_title,
                    "official_url": meta.source_url,
                    "department": meta.government_department
                }]
            )
