from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from pathlib import Path
import shutil
from datetime import datetime

from app.core.database import get_db
from app.core.config import settings
from app.models.chromatographic_analysis import ChromatographicAnalysis
from app.models.material import Material
from app.schemas.chromatographic_analysis import (
    ChromatographicAnalysisResponse,
    ChromatographicAnalysisCreate
)
from app.parsers.csv_parser import ChromatographicCSVParser

router = APIRouter(prefix="/chromatographic-analyses", tags=["chromatographic-analyses"])


@router.post("", response_model=ChromatographicAnalysisResponse, status_code=status.HTTP_201_CREATED)
async def upload_chromatographic_analysis(
    file: UploadFile = File(...),
    material_id: int = Form(...),
    batch_number: Optional[str] = Form(None),
    supplier: Optional[str] = Form(None),
    analysis_date: Optional[str] = Form(None),
    lab_technician: Optional[str] = Form(None),
    weight: float = Form(1.0),
    db: Session = Depends(get_db)
):
    """Upload and parse a chromatographic analysis CSV file"""
    
    # Verify material exists
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Material {material_id} not found"
        )
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are supported"
        )
    
    # Create upload directory if it doesn't exist
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Save file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{material.reference_code}_{timestamp}_{file.filename}"
    file_path = upload_dir / filename
    
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Parse CSV
    parser = ChromatographicCSVParser()
    parse_result = parser.parse_file(str(file_path))
    
    # Parse analysis_date if provided
    parsed_date = None
    if analysis_date:
        try:
            parsed_date = datetime.fromisoformat(analysis_date)
        except ValueError:
            pass
    
    # Create database record
    analysis = ChromatographicAnalysis(
        material_id=material_id,
        filename=file.filename,
        file_path=str(file_path),
        batch_number=batch_number,
        supplier=supplier,
        analysis_date=parsed_date,
        lab_technician=lab_technician,
        weight=weight,
        parsed_data=parse_result,
        is_processed=1 if parse_result['success'] else -1,
        processing_notes="; ".join(parse_result.get('validation_errors', []))
    )
    
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    
    return analysis


@router.get("/material/{material_id}", response_model=List[ChromatographicAnalysisResponse])
def get_material_analyses(
    material_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all chromatographic analyses for a material"""
    analyses = db.query(ChromatographicAnalysis).filter(
        ChromatographicAnalysis.material_id == material_id
    ).order_by(ChromatographicAnalysis.created_at.desc()).offset(skip).limit(limit).all()
    
    return analyses


@router.get("/{analysis_id}", response_model=ChromatographicAnalysisResponse)
def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """Get a specific chromatographic analysis"""
    analysis = db.query(ChromatographicAnalysis).filter(
        ChromatographicAnalysis.id == analysis_id
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis {analysis_id} not found"
        )
    
    return analysis


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """Delete a chromatographic analysis"""
    analysis = db.query(ChromatographicAnalysis).filter(
        ChromatographicAnalysis.id == analysis_id
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis {analysis_id} not found"
        )
    
    # Delete file if exists
    file_path = Path(analysis.file_path)
    if file_path.exists():
        file_path.unlink()
    
    db.delete(analysis)
    db.commit()
    
    return None








