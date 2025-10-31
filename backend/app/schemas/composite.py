from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.composite import CompositeOrigin, CompositeStatus, ComponentType, CompositeType


class CompositeComponentBase(BaseModel):
    """Base composite component schema"""
    cas_number: Optional[str] = None
    component_name: str
    percentage: float = Field(..., ge=0, le=100)
    component_type: ComponentType = ComponentType.COMPONENT
    confidence_level: Optional[float] = Field(None, ge=0, le=100)
    notes: Optional[str] = None


class CompositeComponentResponse(CompositeComponentBase):
    """Schema for composite component response"""
    id: int
    composite_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CompositeBase(BaseModel):
    """Base composite schema"""
    material_id: int
    origin: CompositeOrigin
    composite_type: Optional[CompositeType] = None
    questionnaire_id: Optional[int] = None
    source_documents: Optional[List[Dict[str, Any]]] = None
    extraction_confidence: Optional[float] = Field(None, ge=0, le=100)
    composite_metadata: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class CompositeCreate(CompositeBase):
    """Schema for creating a composite"""
    components: List[CompositeComponentBase]

    @validator('components')
    def validate_components_sum(cls, v):
        total = sum(c.percentage for c in v)
        if not (99.0 <= total <= 101.0):  # Allow small rounding errors
            raise ValueError(f'Component percentages must sum to ~100%, got {total}%')
        return v


class CompositeCalculateRequest(BaseModel):
    """Schema for calculating a composite"""
    material_id: int
    origin: CompositeOrigin = CompositeOrigin.LAB
    analysis_ids: Optional[List[int]] = None  # Specific analyses to use, or all if None
    notes: Optional[str] = None


class CompositeResponse(CompositeBase):
    """Schema for composite response"""
    id: int
    version: int
    status: CompositeStatus
    composite_type: Optional[CompositeType] = None
    questionnaire_id: Optional[int] = None
    extraction_confidence: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime]
    approved_at: Optional[datetime]
    components: List[CompositeComponentResponse]

    class Config:
        from_attributes = True


class ComponentComparison(BaseModel):
    """Component comparison between versions"""
    component_name: str
    cas_number: Optional[str]
    old_percentage: Optional[float]
    new_percentage: Optional[float]
    change: float  # Percentage point change
    change_percent: Optional[float]  # Percent change relative to old value


class CompositeCompareResponse(BaseModel):
    """Schema for composite comparison"""
    old_composite_id: int
    new_composite_id: int
    old_version: int
    new_version: int
    components_added: List[ComponentComparison]
    components_removed: List[ComponentComparison]
    components_changed: List[ComponentComparison]
    significant_changes: bool
    total_change_score: float

