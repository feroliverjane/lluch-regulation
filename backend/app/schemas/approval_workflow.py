from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.approval_workflow import WorkflowStatus


class ApprovalWorkflowBase(BaseModel):
    """Base approval workflow schema"""
    composite_id: int
    assigned_to_id: Optional[int] = None
    review_comments: Optional[str] = None


class ApprovalActionRequest(BaseModel):
    """Schema for approval action (approve/reject)"""
    action: str  # "approve" or "reject"
    comments: Optional[str] = None
    rejection_reason: Optional[str] = None


class ApprovalWorkflowResponse(ApprovalWorkflowBase):
    """Schema for approval workflow response"""
    id: int
    assigned_by_id: Optional[int]
    status: WorkflowStatus
    rejection_reason: Optional[str]
    created_at: datetime
    assigned_at: Optional[datetime]
    reviewed_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True








