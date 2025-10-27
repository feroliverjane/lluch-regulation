from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.approval_workflow import ApprovalWorkflow, WorkflowStatus
from app.schemas.approval_workflow import ApprovalWorkflowResponse

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("", response_model=List[ApprovalWorkflowResponse])
def list_workflows(
    status_filter: Optional[WorkflowStatus] = None,
    assigned_to_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all approval workflows"""
    query = db.query(ApprovalWorkflow)
    
    if status_filter:
        query = query.filter(ApprovalWorkflow.status == status_filter)
    
    if assigned_to_id:
        query = query.filter(ApprovalWorkflow.assigned_to_id == assigned_to_id)
    
    workflows = query.order_by(ApprovalWorkflow.created_at.desc()).offset(skip).limit(limit).all()
    
    return workflows


@router.get("/{workflow_id}", response_model=ApprovalWorkflowResponse)
def get_workflow(workflow_id: int, db: Session = Depends(get_db)):
    """Get a specific workflow"""
    workflow = db.query(ApprovalWorkflow).filter(
        ApprovalWorkflow.id == workflow_id
    ).first()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )
    
    return workflow


@router.get("/composite/{composite_id}", response_model=ApprovalWorkflowResponse)
def get_composite_workflow(composite_id: int, db: Session = Depends(get_db)):
    """Get workflow for a specific composite"""
    workflow = db.query(ApprovalWorkflow).filter(
        ApprovalWorkflow.composite_id == composite_id
    ).first()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No workflow found for composite {composite_id}"
        )
    
    return workflow






