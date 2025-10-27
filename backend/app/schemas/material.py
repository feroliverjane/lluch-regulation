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


class MaterialResponse(MaterialBase):
    """Schema for material response"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True








