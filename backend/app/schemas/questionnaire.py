from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


# Enums
class QuestionnaireTypeSchema(str, Enum):
    INITIAL_HOMOLOGATION = "INITIAL_HOMOLOGATION"
    REHOMOLOGATION = "REHOMOLOGATION"


class QuestionnaireStatusSchema(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REQUIRES_REVISION = "REQUIRES_REVISION"


class ValidationTypeSchema(str, Enum):
    BLUE_LINE_COMPARISON = "BLUE_LINE_COMPARISON"
    VERSION_COMPARISON = "VERSION_COMPARISON"
    AI_RISK_ASSESSMENT = "AI_RISK_ASSESSMENT"


class ValidationSeveritySchema(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class IncidentStatusSchema(str, Enum):
    OPEN = "OPEN"
    ESCALATED_TO_SUPPLIER = "ESCALATED_TO_SUPPLIER"
    RESOLVED = "RESOLVED"
    OVERRIDDEN = "OVERRIDDEN"


class ResolutionActionSchema(str, Enum):
    SUPPLIER_CORRECTION = "SUPPLIER_CORRECTION"
    USER_OVERRIDE = "USER_OVERRIDE"
    ESCALATED = "ESCALATED"
    PENDING = "PENDING"


# Questionnaire Schemas
class QuestionnaireBase(BaseModel):
    material_id: int
    supplier_code: str
    questionnaire_type: QuestionnaireTypeSchema
    responses: Dict[str, Any] = Field(default_factory=dict)


class QuestionnaireCreate(QuestionnaireBase):
    version: Optional[int] = 1
    previous_version_id: Optional[int] = None


class QuestionnaireUpdate(BaseModel):
    responses: Optional[Dict[str, Any]] = None
    status: Optional[QuestionnaireStatusSchema] = None


class QuestionnaireResponse(QuestionnaireBase):
    id: int
    version: int
    previous_version_id: Optional[int] = None
    status: QuestionnaireStatusSchema
    ai_risk_score: Optional[int] = None
    ai_summary: Optional[str] = None
    ai_recommendation: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Validation Schemas
class QuestionnaireValidationResponse(BaseModel):
    id: int
    questionnaire_id: int
    validation_type: ValidationTypeSchema
    field_name: str
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    deviation_percentage: Optional[float] = None
    severity: ValidationSeveritySchema
    requires_action: bool
    ai_analysis: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Incident Schemas
class QuestionnaireIncidentCreate(BaseModel):
    questionnaire_id: int
    validation_id: Optional[int] = None
    field_name: str
    issue_description: str
    assigned_to_id: Optional[int] = None


class QuestionnaireIncidentUpdate(BaseModel):
    status: Optional[IncidentStatusSchema] = None
    resolution_action: Optional[ResolutionActionSchema] = None
    override_justification: Optional[str] = None
    resolution_notes: Optional[str] = None
    assigned_to_id: Optional[int] = None


class QuestionnaireIncidentResponse(BaseModel):
    id: int
    questionnaire_id: int
    validation_id: Optional[int] = None
    field_name: str
    issue_description: str
    status: IncidentStatusSchema
    resolution_action: ResolutionActionSchema
    assigned_to_id: Optional[int] = None
    created_by_id: Optional[int] = None
    override_justification: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    supplier_notified_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# AI Analysis Response
class AIAnalysisResponse(BaseModel):
    risk_score: int = Field(..., ge=0, le=100, description="Risk score from 0-100")
    summary: str
    recommendation: str  # "APPROVE", "REVIEW", "REJECT"
    confidence: float = Field(..., ge=0, le=1, description="AI confidence 0-1")
    key_findings: List[str]
    areas_of_concern: List[str]


# Comparison Response
class QuestionnaireComparisonResponse(BaseModel):
    current_version: int
    previous_version: Optional[int] = None
    changes: List[Dict[str, Any]]
    added_fields: List[str]
    removed_fields: List[str]
    modified_fields: List[str]
    summary: str


# Submit Request
class QuestionnaireSubmitRequest(BaseModel):
    pass  # No additional data needed for submission


# Incident Action Requests
class IncidentEscalateRequest(BaseModel):
    notes: Optional[str] = None


class IncidentOverrideRequest(BaseModel):
    justification: str = Field(..., min_length=10, description="Justification required for override")


class IncidentResolveRequest(BaseModel):
    resolution_notes: str

