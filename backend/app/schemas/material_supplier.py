from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MaterialSupplierStatusSchema(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class MismatchField(BaseModel):
    """Structure for a mismatched field"""
    field_code: str
    field_name: str
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    severity: str = "WARNING"  # CRITICAL, WARNING, INFO
    accepted: bool = False


class ComparisonResult(BaseModel):
    """Result of comparing questionnaire with Blue Line"""
    blue_line_exists: bool
    matches: int = 0
    mismatches: List[MismatchField] = Field(default_factory=list)
    score: int = 0  # 0-100 validation score
    message: Optional[str] = None


class MaterialSupplierBase(BaseModel):
    """Base schema for MaterialSupplier"""
    material_id: int
    questionnaire_id: int
    supplier_code: str
    supplier_name: Optional[str] = None
    blue_line_id: Optional[int] = None
    status: MaterialSupplierStatusSchema = MaterialSupplierStatusSchema.ACTIVE
    validation_score: int = Field(default=0, ge=0, le=100)
    mismatch_fields: List[Dict[str, Any]] = Field(default_factory=list)
    accepted_mismatches: List[str] = Field(default_factory=list)  # List of fieldCodes


class MaterialSupplierCreate(BaseModel):
    """Schema for creating a MaterialSupplier"""
    questionnaire_id: int
    accepted_mismatches: Optional[List[str]] = Field(default_factory=list)


class MaterialSupplierUpdate(BaseModel):
    """Schema for updating a MaterialSupplier"""
    status: Optional[MaterialSupplierStatusSchema] = None
    accepted_mismatches: Optional[List[str]] = None


class MaterialSupplierResponse(MaterialSupplierBase):
    """Schema for MaterialSupplier response"""
    id: int
    validated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AcceptMismatchesRequest(BaseModel):
    """Request to accept specific mismatches"""
    accepted_mismatches: List[str] = Field(default_factory=list)  # List of fieldCodes to accept

