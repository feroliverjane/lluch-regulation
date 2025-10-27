from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class WorkflowStatus(str, enum.Enum):
    """Workflow status"""
    PENDING = "PENDING"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    # Blue Line specific states
    APC = "APC"  # Approved Conditionally
    APR = "APR"  # Approved Regulatory
    REJ = "REJ"  # Rejected (Blue Line specific)
    CAN = "CAN"  # Cancelled (Blue Line specific)
    EXP = "EXP"  # Expired
    INC = "INC"  # Incomplete
    REA = "REA"  # Ready
    RUN = "RUN"  # Running
    VAL = "VAL"  # Validation


class ApprovalWorkflow(Base):
    """Approval workflow for composites"""
    __tablename__ = "approval_workflows"

    id = Column(Integer, primary_key=True, index=True)
    composite_id = Column(Integer, ForeignKey("composites.id"), nullable=False, unique=True)
    
    # Assignment
    assigned_to_id = Column(Integer, ForeignKey("users.id"))
    assigned_by_id = Column(Integer, ForeignKey("users.id"))
    
    # Status
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.PENDING)
    
    # Blue Line specific: Section-based status tracking
    section = Column(String(50))  # "Regulatory" or "Technical"
    regulatory_status = Column(String(20))  # Track Regulatory section state (APC, APR, etc.)
    technical_status = Column(String(20))  # Track Technical section state (to detect REJ)
    
    # Review details
    review_comments = Column(Text)
    rejection_reason = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    assigned_at = Column(DateTime(timezone=True))
    reviewed_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    composite = relationship("Composite", back_populates="workflow")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id], backref="assigned_workflows")
    assigned_by = relationship("User", foreign_keys=[assigned_by_id], backref="created_workflows")

    def __repr__(self):
        return f"<ApprovalWorkflow(id={self.id}, composite_id={self.composite_id}, status={self.status})>"






