from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import shutil
import logging

from app.core.database import get_db
from app.core.config import settings
from app.models.composite import Composite, CompositeStatus, CompositeType, CompositeComponent, CompositeOrigin
from app.models.approval_workflow import ApprovalWorkflow, WorkflowStatus
from app.schemas.composite import (
    CompositeCreate,
    CompositeResponse,
    CompositeCalculateRequest,
    CompositeCompareResponse
)
from app.services.composite_calculator import CompositeCalculator
from app.services.composite_comparator import CompositeComparator
from app.parsers.composite_excel_parser import CompositeExcelParser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/composites", tags=["composites"])


@router.post("/calculate", response_model=CompositeResponse, status_code=status.HTTP_201_CREATED)
def calculate_composite(
    request: CompositeCalculateRequest,
    db: Session = Depends(get_db)
):
    """Calculate a composite from chromatographic analyses"""
    calculator = CompositeCalculator(db)
    
    try:
        composite = calculator.calculate_from_lab_analyses(
            material_id=request.material_id,
            analysis_ids=request.analysis_ids,
            notes=request.notes
        )
        
        db.add(composite)
        db.commit()
        db.refresh(composite)
        
        return composite
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("", response_model=CompositeResponse, status_code=status.HTTP_201_CREATED)
def create_composite(
    composite_data: CompositeCreate,
    db: Session = Depends(get_db)
):
    """Create a composite manually"""
    calculator = CompositeCalculator(db)
    
    try:
        # Extract components from composite_data
        components_list = [comp.model_dump() for comp in composite_data.components]
        
        composite = calculator.calculate_from_documents(
            material_id=composite_data.material_id,
            components_data=components_list,
            notes=composite_data.notes
        )
        
        # Update origin and metadata
        composite.origin = composite_data.origin
        if composite_data.composite_metadata:
            composite.composite_metadata = composite_data.composite_metadata
        
        db.add(composite)
        db.commit()
        db.refresh(composite)
        
        return composite
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{composite_id}", response_model=CompositeResponse)
def get_composite(composite_id: int, db: Session = Depends(get_db)):
    """Get a specific composite"""
    composite = db.query(Composite).filter(Composite.id == composite_id).first()
    
    if not composite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Composite {composite_id} not found"
        )
    
    return composite


@router.get("/material/{material_id}", response_model=List[CompositeResponse])
def get_material_composites(
    material_id: int,
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[CompositeStatus] = None,
    db: Session = Depends(get_db)
):
    """Get all composites for a material"""
    query = db.query(Composite).filter(Composite.material_id == material_id)
    
    if status_filter:
        query = query.filter(Composite.status == status_filter)
    
    composites = query.order_by(Composite.version.desc()).offset(skip).limit(limit).all()
    
    return composites


@router.get("/{composite_id}/compare/{other_composite_id}", response_model=CompositeCompareResponse)
def compare_composites(
    composite_id: int,
    other_composite_id: int,
    db: Session = Depends(get_db)
):
    """Compare two composite versions"""
    comparator = CompositeComparator(db)
    
    try:
        comparison = comparator.compare_composites(composite_id, other_composite_id)
        return comparison
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/{composite_id}/submit-for-approval", response_model=CompositeResponse)
def submit_for_approval(
    composite_id: int,
    assigned_to_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Submit a composite for approval"""
    composite = db.query(Composite).filter(Composite.id == composite_id).first()
    
    if not composite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Composite {composite_id} not found"
        )
    
    if composite.status != CompositeStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only DRAFT composites can be submitted for approval"
        )
    
    # Update status
    composite.status = CompositeStatus.PENDING_APPROVAL
    
    # Create or update workflow
    workflow = db.query(ApprovalWorkflow).filter(
        ApprovalWorkflow.composite_id == composite_id
    ).first()
    
    if not workflow:
        workflow = ApprovalWorkflow(
            composite_id=composite_id,
            status=WorkflowStatus.PENDING,
            assigned_to_id=assigned_to_id
        )
        db.add(workflow)
    else:
        workflow.status = WorkflowStatus.PENDING
        workflow.assigned_to_id = assigned_to_id
    
    if assigned_to_id:
        workflow.assigned_at = datetime.now()
    
    db.commit()
    db.refresh(composite)
    
    return composite


@router.put("/{composite_id}/approve", response_model=CompositeResponse)
def approve_composite(
    composite_id: int,
    comments: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Approve a composite"""
    composite = db.query(Composite).filter(Composite.id == composite_id).first()
    
    if not composite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Composite {composite_id} not found"
        )
    
    if composite.status != CompositeStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PENDING_APPROVAL composites can be approved"
        )
    
    # Update composite
    composite.status = CompositeStatus.APPROVED
    composite.approved_at = datetime.now()
    
    # Update workflow
    workflow = db.query(ApprovalWorkflow).filter(
        ApprovalWorkflow.composite_id == composite_id
    ).first()
    
    if workflow:
        workflow.status = WorkflowStatus.APPROVED
        workflow.review_comments = comments
        workflow.reviewed_at = datetime.now()
        workflow.completed_at = datetime.now()
    
    db.commit()
    db.refresh(composite)
    
    return composite


@router.put("/{composite_id}/reject", response_model=CompositeResponse)
def reject_composite(
    composite_id: int,
    reason: str,
    comments: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Reject a composite"""
    composite = db.query(Composite).filter(Composite.id == composite_id).first()
    
    if not composite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Composite {composite_id} not found"
        )
    
    if composite.status != CompositeStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PENDING_APPROVAL composites can be rejected"
        )
    
    # Update composite
    composite.status = CompositeStatus.REJECTED
    
    # Update workflow
    workflow = db.query(ApprovalWorkflow).filter(
        ApprovalWorkflow.composite_id == composite_id
    ).first()
    
    if workflow:
        workflow.status = WorkflowStatus.REJECTED
        workflow.rejection_reason = reason
        workflow.review_comments = comments
        workflow.reviewed_at = datetime.now()
        workflow.completed_at = datetime.now()
    
    db.commit()
    db.refresh(composite)
    
    return composite


@router.delete("/{composite_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_composite(composite_id: int, db: Session = Depends(get_db)):
    """Delete a composite (only if DRAFT or REJECTED)"""
    composite = db.query(Composite).filter(Composite.id == composite_id).first()
    
    if not composite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Composite {composite_id} not found"
        )
    
    if composite.status not in [CompositeStatus.DRAFT, CompositeStatus.REJECTED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only DRAFT or REJECTED composites can be deleted"
        )
    
    db.delete(composite)
    db.commit()
    
    return None


# ===== NEW COMPOSITE COMPARISON AND AVERAGING =====

@router.post("/average", response_model=CompositeResponse)
def create_average_composite(
    composite_a_id: int,
    composite_b_id: int,
    target_material_id: int,
    db: Session = Depends(get_db)
):
    """
    Create average composite from two composites.
    Used for Z1 composite updates.
    """
    from app.services.composite_comparison_service import CompositeComparisonService
    
    comparison_service = CompositeComparisonService(db)
    
    try:
        averaged_composite = comparison_service.calculate_average_composite(
            composite_a_id,
            composite_b_id,
            target_material_id
        )
        
        db.add(averaged_composite)
        db.commit()
        db.refresh(averaged_composite)
        
        return averaged_composite
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating average composite: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating average composite: {str(e)}"
        )


@router.post("/compare-detailed", response_model=dict)
def compare_composites_detailed(
    composite_a_id: int,
    composite_b_id: int,
    db: Session = Depends(get_db)
):
    """
    Compare two composites in detail.
    Returns components added, removed, changed with match score.
    """
    from app.services.composite_comparison_service import CompositeComparisonService
    
    comparison_service = CompositeComparisonService(db)
    
    try:
        comparison_result = comparison_service.compare_composites(
            composite_a_id,
            composite_b_id
        )
        
        return comparison_result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{composite_id}/import-z2-from-excel", response_model=CompositeResponse)
async def import_z2_from_excel(
    composite_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Import composite Z2 from Excel/CSV file (SAP format).
    Updates an existing Z1 composite to Z2 with data from the Excel file.
    
    The Excel/CSV should have columns:
    - Espec./compon. or CAS: CAS number
    - Nombre del producto: Component name
    - Cl.Componente: Must be 'COMPONENT' for main components
    - Valor Lím.inf. and Valor Lím.sup.: Percentage range
    - Unidad: Unit (usually '%')
    """
    composite = db.query(Composite).filter(Composite.id == composite_id).first()
    
    if not composite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Composite {composite_id} not found"
        )
    
    # Validate file type
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ['.xlsx', '.xls', '.csv']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato de archivo no soportado: {file_ext}. Use .xlsx, .xls o .csv"
        )
    
    # Save file temporarily
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"composite_z2_{timestamp}_{file.filename}"
    file_path = upload_dir / filename
    
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Parse Excel/CSV
        parser = CompositeExcelParser()
        parse_result = parser.parse_file(str(file_path))
        
        if not parse_result["success"]:
            errors = parse_result.get("errors", [])
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Error parseando archivo: {'; '.join(errors)}"
            )
        
        components_data = parse_result["components"]
        
        if not components_data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No se encontraron componentes en el archivo"
            )
        
        logger.info(f"Importando {len(components_data)} componentes desde Excel para composite {composite_id}")
        
        # Delete existing components
        for comp in composite.components:
            db.delete(comp)
        
        # Add new components from Excel
        for comp_data in components_data:
            component = CompositeComponent(
                composite_id=composite_id,
                cas_number=comp_data.get("cas_number"),
                component_name=comp_data["component_name"],
                percentage=comp_data["percentage"],
                component_type=comp_data.get("component_type", "COMPONENT"),
                notes=f"Importado desde Excel: {comp_data.get('percentage_min', 0)}-{comp_data.get('percentage_max', 0)}%"
            )
            composite.components.append(component)
        
        # Update composite to Z2
        composite.composite_type = CompositeType.Z2
        composite.origin = CompositeOrigin.MANUAL  # Z2 imported manually
        
        # Update metadata
        existing_metadata = composite.composite_metadata or {}
        existing_metadata.update({
            "import_source": "excel",
            "import_filename": file.filename,
            "import_date": datetime.utcnow().isoformat(),
            "total_percentage": parse_result.get("total_percentage", 0)
        })
        composite.composite_metadata = existing_metadata
        composite.notes = f"Composite Z2 importado desde {file.filename} con {len(components_data)} componentes"
        
        db.commit()
        db.refresh(composite)
        
        logger.info(f"Composite {composite_id} actualizado a Z2 con {len(components_data)} componentes")
        
        return composite
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error importando Z2 desde Excel: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error importando composite Z2: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                logger.warning(f"No se pudo eliminar archivo temporal {file_path}: {e}")

