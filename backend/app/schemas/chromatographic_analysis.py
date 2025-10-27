from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class ChromatographicAnalysisBase(BaseModel):
    """Base chromatographic analysis schema"""
    material_id: int
    batch_number: Optional[str] = Field(None, max_length=100)
    supplier: Optional[str] = Field(None, max_length=200)
    analysis_date: Optional[datetime] = None
    lab_technician: Optional[str] = Field(None, max_length=200)
    weight: float = Field(1.0, ge=0)


class ChromatographicAnalysisCreate(ChromatographicAnalysisBase):
    """Schema for creating a chromatographic analysis"""
    pass


class ChromatographicAnalysisResponse(ChromatographicAnalysisBase):
    """Schema for chromatographic analysis response"""
    id: int
    filename: str
    file_path: str
    parsed_data: Optional[Dict[str, Any]]
    is_processed: int
    processing_notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True






