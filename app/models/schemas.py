from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class IntentType(str, Enum):
    DISCOVER_SCHEMES = "DISCOVER_SCHEMES"
    ELIGIBILITY_CHECK = "ELIGIBILITY_CHECK"
    APPLICATION_GUIDANCE = "APPLICATION_GUIDANCE"
    GENERAL_SCHEME_INFORMATION = "GENERAL_SCHEME_INFORMATION"

class CitizenProfile(BaseModel):
    age: Optional[int] = Field(default=None, description="Age in years")
    gender: Optional[str] = Field(default=None, description="Male, Female, Other")
    state: Optional[str] = Field(default=None, description="State of residence e.g. Karnataka")
    district: Optional[str] = Field(default=None, description="District if specified")
    occupation: Optional[str] = Field(default=None, description="e.g. Farmer, Student, Street Vendor, Unemployed")
    annual_income: Optional[float] = Field(default=None, description="Annual family income in INR")
    monthly_income: Optional[float] = Field(default=None, description="Monthly income in INR")
    category: Optional[str] = Field(default=None, description="Social category: SC, ST, OBC, General")
    land_ownership_acres: Optional[float] = Field(default=None, description="Cultivable land owned in acres")
    is_farmer: Optional[bool] = Field(default=None, description="Whether the citizen is a farmer")
    is_student: Optional[bool] = Field(default=None, description="Whether the citizen is currently a student")
    is_tax_payer: Optional[bool] = Field(default=None, description="Whether the citizen pays income tax")
    has_disability: Optional[bool] = Field(default=None, description="Whether applicant has disability")
    additional_notes: Optional[str] = Field(default=None, description="Other pertinent notes from citizen")

    def merge_with(self, other: "CitizenProfile") -> "CitizenProfile":
        """Merge another profile into this one, letting explicit values overwrite None."""
        data = self.model_dump()
        for k, v in other.model_dump().items():
            if v is not None:
                data[k] = v
        return CitizenProfile(**data)

class IntentDetectionResult(BaseModel):
    intent: IntentType
    confidence: float = 1.0
    target_scheme: Optional[str] = None
    extracted_profile: CitizenProfile = Field(default_factory=CitizenProfile)
    safe_summary: str = Field(default="", description="Safe summary for execution trace")

class DocumentChunkMetadata(BaseModel):
    scheme_id: str
    scheme_name: str
    source_title: str
    source_url: str
    government_department: str
    document_type: str = "official_scheme_guidelines"
    section: str = "general"

class DocumentChunk(BaseModel):
    id: str
    content: str
    metadata: DocumentChunkMetadata
    score: Optional[float] = None

class ConditionStatus(str, Enum):
    MET = "MET"
    NOT_MET = "NOT_MET"
    MISSING_INFO = "MISSING_INFO"

class ConditionCheck(BaseModel):
    criterion: str
    status: ConditionStatus
    official_rule: str
    citizen_evidence: str

class SchemeEvaluation(BaseModel):
    scheme_id: str
    scheme_name: str
    status: str = Field(description="Eligible | Possibly eligible — missing information | Not eligible | Eligibility cannot be determined")
    conditions_met: List[str] = Field(default_factory=list)
    conditions_failed: List[str] = Field(default_factory=list)
    missing_fields: List[str] = Field(default_factory=list)
    official_sources: List[Dict[str, str]] = Field(default_factory=list)
    summary: str = ""

class ApplicationGuidance(BaseModel):
    scheme_name: str
    official_portal_url: str
    offline_option: Optional[str] = None
    steps: List[str] = Field(default_factory=list)
    required_documents: List[str] = Field(default_factory=list)
    important_notes: Optional[str] = None
    official_sources: List[Dict[str, str]] = Field(default_factory=list)

class ExecutionTraceStep(BaseModel):
    agent: str
    action: str
    summary: str
    details: Dict[str, Any] = Field(default_factory=dict)

class WorkflowResult(BaseModel):
    query: str
    intent: IntentType
    citizen_profile: CitizenProfile
    retrieval_needed: bool
    retrieved_chunks_count: int
    evaluations: List[SchemeEvaluation] = Field(default_factory=list)
    application_guidance: Optional[ApplicationGuidance] = None
    missing_fields_prompt: List[str] = Field(default_factory=list)
    response_text: str = ""
    citations: List[Dict[str, str]] = Field(default_factory=list)
    execution_trace: List[ExecutionTraceStep] = Field(default_factory=list)
