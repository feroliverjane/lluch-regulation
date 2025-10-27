from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class MaterialBase(BaseModel):
    """Base material schema"""
    reference_code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    supplier: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    cas_number: Optional[str] = Field(None, max_length=50)
    material_type: Optional[str] = Field(None, max_length=50)
    # Blue Line fields
    sap_status: Optional[str] = Field(None, max_length=10)
    supplier_code: Optional[str] = Field(None, max_length=100)
    lluch_reference: Optional[str] = Field(None, max_length=100)
    last_purchase_date: Optional[datetime] = None


class MaterialCreate(MaterialBase):
    """Schema for creating a material"""
    pass


class MaterialUpdate(BaseModel):
    """Schema for updating a material"""
    name: Optional[str] = Field(None, max_length=200)
    supplier: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    cas_number: Optional[str] = Field(None, max_length=50)
    material_type: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    # Blue Line fields
    sap_status: Optional[str] = Field(None, max_length=10)
    supplier_code: Optional[str] = Field(None, max_length=100)
    lluch_reference: Optional[str] = Field(None, max_length=100)
    last_purchase_date: Optional[datetime] = None


class MaterialResponse(MaterialBase):
    """Schema for material response"""
    id: int
    is_active: bool
    is_blue_line_eligible: Optional[bool] = False
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True






