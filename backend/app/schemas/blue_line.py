from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class BlueLineMaterialTypeSchema(str, Enum):
    """Blue Line material type"""
    Z001 = "Z001"  # Provisional estimated (worst case)
    Z002 = "Z002"  # Homologated (Lluch analysis)


class BlueLineSyncStatusSchema(str, Enum):
    """Synchronization status"""
    PENDING = "PENDING"
    SYNCED = "SYNCED"
    FAILED = "FAILED"
    NOT_REQUIRED = "NOT_REQUIRED"


class BlueLineBase(BaseModel):
    """Base Blue Line schema"""
    material_id: int
    template_id: Optional[int] = None
    responses: Dict[str, Any] = Field(default_factory=dict)
    blue_line_data: Dict[str, Any] = Field(default_factory=dict)  # Legacy, for backward compatibility
    material_type: BlueLineMaterialTypeSchema
    composite_id: Optional[int] = None
    calculation_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class BlueLineCreate(BlueLineBase):
    """Schema for creating a Blue Line"""
    pass


class BlueLineUpdate(BaseModel):
    """Schema for updating a Blue Line"""
    template_id: Optional[int] = None
    responses: Optional[Dict[str, Any]] = None
    blue_line_data: Optional[Dict[str, Any]] = None
    material_type: Optional[BlueLineMaterialTypeSchema] = None
    composite_id: Optional[int] = None
    calculation_metadata: Optional[Dict[str, Any]] = None
    sync_status: Optional[BlueLineSyncStatusSchema] = None


class BlueLineResponse(BlueLineBase):
    """Schema for Blue Line response"""
    id: int
    template_id: Optional[int] = None
    responses: Dict[str, Any] = Field(default_factory=dict)
    composite_id: Optional[int] = None
    sync_status: BlueLineSyncStatusSchema
    last_synced_at: Optional[datetime] = None
    sync_error_message: Optional[str] = None
    calculated_at: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None

    @field_validator('responses', mode='before')
    @classmethod
    def ensure_responses_is_dict(cls, v):
        """Ensure responses is always a dict, not None"""
        return v if v is not None else {}
    
    @field_validator('blue_line_data', mode='before')
    @classmethod
    def ensure_blue_line_data_is_dict(cls, v):
        """Ensure blue_line_data is always a dict, not None"""
        return v if v is not None else {}

    class Config:
        from_attributes = True


class BlueLineCalculateRequest(BaseModel):
    """Schema for calculating a Blue Line"""
    material_id: int
    force_recalculate: bool = False


class BlueLineSyncRequest(BaseModel):
    """Schema for sync request"""
    blue_line_id: int
    direction: str = Field(..., pattern="^(to_sap|from_sap)$")


class BlueLineSyncResponse(BaseModel):
    """Schema for sync response"""
    success: bool
    message: str
    sync_status: BlueLineSyncStatusSchema
    synced_at: Optional[datetime] = None
    error_details: Optional[str] = None


class BlueLineEligibilityCheck(BaseModel):
    """Schema for eligibility check result"""
    material_id: int
    is_eligible: bool
    reasons: List[str] = Field(default_factory=list)
    has_purchase_history: bool
    regulatory_status_ok: bool
    technical_status_ok: bool
    purchase_date: Optional[datetime] = None


# Field Logic Schemas

class FieldTypeSchema(str, Enum):
    """Field type for Blue Line fields"""
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    BOOLEAN = "boolean"
    CALCULATED = "calculated"
    SELECTION = "selection"


class BlueLineFieldLogicBase(BaseModel):
    """Base schema for field logic"""
    field_name: str
    field_label: Optional[str] = None
    field_category: Optional[str] = None
    field_type: FieldTypeSchema
    material_type_filter: str = "ALL"
    logic_expression: Dict[str, Any]
    priority: int = 100
    validation_rules: Optional[Dict[str, Any]] = None
    is_active: bool = True
    description: Optional[str] = None
    example_value: Optional[str] = None
    notes: Optional[str] = None


class BlueLineFieldLogicCreate(BlueLineFieldLogicBase):
    """Schema for creating field logic"""
    pass


class BlueLineFieldLogicUpdate(BaseModel):
    """Schema for updating field logic"""
    field_label: Optional[str] = None
    field_category: Optional[str] = None
    field_type: Optional[FieldTypeSchema] = None
    material_type_filter: Optional[str] = None
    logic_expression: Optional[Dict[str, Any]] = None
    priority: Optional[int] = None
    validation_rules: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None
    example_value: Optional[str] = None
    notes: Optional[str] = None


class BlueLineFieldLogicResponse(BlueLineFieldLogicBase):
    """Schema for field logic response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BlueLineFieldLogicBulkImport(BaseModel):
    """Schema for bulk importing field logics"""
    field_logics: List[BlueLineFieldLogicCreate]
    overwrite_existing: bool = False

