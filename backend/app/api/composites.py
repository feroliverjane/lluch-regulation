from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.composite import Composite, CompositeStatus
from app.models.approval_workflow import ApprovalWorkflow, WorkflowStatus
from app.schemas.composite import (
    CompositeCreate,
    CompositeResponse,
    CompositeCalculateRequest,
    CompositeCompareResponse
)
from app.services.composite_calculator import CompositeCalculator
from app.services.composite_comparator import CompositeComparator

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

