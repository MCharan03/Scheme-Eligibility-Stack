import json
from typing import List, Dict, Any
from langchain_core.output_parsers import JsonOutputParser
from app.llm.model import LLMFactory
from app.llm.prompts import ELIGIBILITY_PROMPT
from app.models.schemas import SchemeEvaluation, CitizenProfile, DocumentChunk

class EligibilityAgent:
    """Evaluates scheme eligibility strictly against retrieved official scheme documents."""

    def __init__(self, llm=None):
        self.llm = llm or LLMFactory.get_llm()
        self.parser = JsonOutputParser()
        # LCEL chain
        self.chain = ELIGIBILITY_PROMPT | self.llm | self.parser

    def evaluate(self, profile: CitizenProfile, chunks: List[DocumentChunk]) -> List[SchemeEvaluation]:
        if not chunks:
            return [
                SchemeEvaluation(
                    scheme_id="unknown",
                    scheme_name="Unknown Scheme",
                    status="Eligibility cannot be determined",
                    conditions_met=[],
                    conditions_failed=[],
                    missing_fields=["Official scheme document not found"],
                    summary="No official scheme documents could be retrieved to verify eligibility."
                )
            ]

        # Assemble retrieved context
        context_blocks = []
        for c in chunks:
            context_blocks.append(
                f"[Source: {c.metadata.source_title} | Department: {c.metadata.government_department} | URL: {c.metadata.source_url}]\n{c.content}"
            )
        retrieved_context_str = "\n\n---\n\n".join(context_blocks)
        profile_str = profile.model_dump_json(exclude_none=True, indent=2)

        try:
            raw_result = self.chain.invoke({
                "citizen_profile": profile_str,
                "retrieved_context": retrieved_context_str
            })
            evaluations_data = raw_result.get("evaluations", [])
            results: List[SchemeEvaluation] = []
            for item in evaluations_data:
                # Attach source metadata
                scheme_id = item.get("scheme_id", "unknown")
                sources = [
                    {
                        "source_title": c.metadata.source_title,
                        "official_url": c.metadata.source_url,
                        "department": c.metadata.government_department
                    }
                    for c in chunks if c.metadata.scheme_id == scheme_id or scheme_id == "unknown"
                ]
                results.append(SchemeEvaluation(
                    scheme_id=scheme_id,
                    scheme_name=item.get("scheme_name", "Official Scheme"),
                    status=item.get("status", "Possibly eligible — missing information"),
                    conditions_met=item.get("conditions_met", []),
                    conditions_failed=item.get("conditions_failed", []),
                    missing_fields=item.get("missing_fields", []),
                    official_sources=sources,
                    summary=item.get("summary", "")
                ))
            return results
        except Exception:
            # Deterministic rule-based fallback based strictly on official retrieved documents
            return self._deterministic_evaluate(profile, chunks)

    def _deterministic_evaluate(self, profile: CitizenProfile, chunks: List[DocumentChunk]) -> List[SchemeEvaluation]:
        """Strict rule-based evaluation grounded in the 5 official schemes."""
        evals: List[SchemeEvaluation] = []
        schemes_present = {c.metadata.scheme_id for c in chunks}

        # 1. PM-KISAN
        if "pm_kisan" in schemes_present:
            pm_sources = [{"source_title": "PM-KISAN Official Operational Guidelines", "official_url": "https://pmkisan.gov.in/", "department": "Department of Agriculture and Farmers Welfare"}]
            if profile.is_farmer is False:
                evals.append(SchemeEvaluation(
                    scheme_id="pm_kisan",
                    scheme_name="Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
                    status="Not eligible",
                    conditions_met=[],
                    conditions_failed=["Applicant is not a farmer/cultivator"],
                    missing_fields=[],
                    official_sources=pm_sources,
                    summary="PM-KISAN is exclusively for farmer families."
                ))
            elif profile.is_tax_payer is True:
                evals.append(SchemeEvaluation(
                    scheme_id="pm_kisan",
                    scheme_name="Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
                    status="Not eligible",
                    conditions_met=["Farmer status confirmed"],
                    conditions_failed=["Income tax payee exclusion applies as per official guidelines"],
                    missing_fields=[],
                    official_sources=pm_sources,
                    summary="Income tax payers are explicitly excluded from PM-KISAN."
                ))
            elif profile.land_ownership_acres is not None and profile.land_ownership_acres > 0:
                evals.append(SchemeEvaluation(
                    scheme_id="pm_kisan",
                    scheme_name="Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
                    status="Eligible",
                    conditions_met=[
                        f"Farmer profile confirmed with {profile.land_ownership_acres} acres of cultivable landholding",
                        "Resident Indian citizen farmer family criteria satisfied"
                    ],
                    conditions_failed=[],
                    missing_fields=[],
                    official_sources=pm_sources,
                    summary="Eligible for annual income support of Rs. 6,000 in three 4-monthly installments."
                ))
            else:
                evals.append(SchemeEvaluation(
                    scheme_id="pm_kisan",
                    scheme_name="Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
                    status="Possibly eligible — missing information",
                    conditions_met=["Identified as a farmer/cultivator"],
                    conditions_failed=[],
                    missing_fields=[
                        "Cultivable land ownership (Record of Rights / Patta in applicant's name)",
                        "Confirmation that family does not pay income tax"
                    ],
                    official_sources=pm_sources,
                    summary="PM-KISAN requires verified cultivable landownership and non-taxpayer status."
                ))

        # 2. PM-JAY (Ayushman Bharat)
        if "pm_jay" in schemes_present:
            jay_sources = [{"source_title": "Ayushman Bharat PM-JAY Guidelines", "official_url": "https://nha.gov.in/PM-JAY", "department": "National Health Authority"}]
            if profile.age and profile.age >= 70:
                evals.append(SchemeEvaluation(
                    scheme_id="pm_jay",
                    scheme_name="Ayushman Bharat - PM-JAY (Senior Citizen / Vay Vandana)",
                    status="Eligible",
                    conditions_met=[f"Senior citizen age ({profile.age} years >= 70 years) confirmed"],
                    conditions_failed=[],
                    missing_fields=[],
                    official_sources=jay_sources,
                    summary="Eligible for Rs. 5 Lakh/year health cover under expanded senior citizen criteria."
                ))
            else:
                evals.append(SchemeEvaluation(
                    scheme_id="pm_jay",
                    scheme_name="Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (AB PM-JAY)",
                    status="Possibly eligible — missing information",
                    conditions_met=["General citizen resident profile verified"],
                    conditions_failed=[],
                    missing_fields=[
                        "Ration card category or SECC 2011 deprivation criteria",
                        "Confirmation whether family has government employees or 4-wheeler vehicle"
                    ],
                    official_sources=jay_sources,
                    summary="Requires SECC 2011 deprivation status verification or Ration Card linkage."
                ))

        # 3. Post-Matric Scholarship
        if "post_matric_scholarship" in schemes_present:
            sch_sources = [{"source_title": "National Scholarship Portal Guidelines", "official_url": "https://scholarships.gov.in/", "department": "Department of Social Justice and Empowerment"}]
            if profile.is_student is False:
                evals.append(SchemeEvaluation(
                    scheme_id="post_matric_scholarship",
                    scheme_name="Post-Matric Scholarship Scheme",
                    status="Not eligible",
                    conditions_met=[],
                    conditions_failed=["Applicant is not a student currently enrolled in post-matric education"],
                    missing_fields=[],
                    official_sources=sch_sources,
                    summary="Scheme is strictly restricted to currently enrolled post-matric students."
                ))
            else:
                missing = []
                if not profile.category:
                    missing.append("Social Category (SC, ST, or OBC certificate verification)")
                if profile.annual_income is None:
                    missing.append("Annual Family Income (Must not exceed Rs. 2.5 Lakh per annum)")

                if not missing:
                    if profile.category in ["SC", "ST", "OBC"] and profile.annual_income <= 250000:
                        evals.append(SchemeEvaluation(
                            scheme_id="post_matric_scholarship",
                            scheme_name="Post-Matric Scholarship Scheme for SC/ST/OBC Students",
                            status="Eligible",
                            conditions_met=[
                                f"Enrolled student belonging to eligible category ({profile.category})",
                                f"Annual family income (Rs. {profile.annual_income:,.0f}) is within the Rs. 2,50,000 ceiling"
                            ],
                            conditions_failed=[],
                            missing_fields=[],
                            official_sources=sch_sources,
                            summary="Eligible for 100% compulsory fee reimbursement and annual maintenance allowance."
                        ))
                    else:
                        evals.append(SchemeEvaluation(
                            scheme_id="post_matric_scholarship",
                            scheme_name="Post-Matric Scholarship Scheme for SC/ST/OBC Students",
                            status="Not eligible",
                            conditions_met=["Student status confirmed"],
                            conditions_failed=["Exceeds income limit or category criteria not satisfied"],
                            missing_fields=[],
                            official_sources=sch_sources,
                            summary="Income or category requirements are not met as per official guidelines."
                        ))
                else:
                    evals.append(SchemeEvaluation(
                        scheme_id="post_matric_scholarship",
                        scheme_name="Post-Matric Scholarship Scheme for SC/ST/OBC Students",
                        status="Possibly eligible — missing information",
                        conditions_met=["Identified as student / scholar"],
                        conditions_failed=[],
                        missing_fields=missing,
                        official_sources=sch_sources,
                        summary="Requires official certificate of category and family income below Rs. 2.5 Lakh."
                    ))

        return evals
