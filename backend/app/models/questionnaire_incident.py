from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class IncidentStatus(str, enum.Enum):
    """Incident status"""
    OPEN = "OPEN"
    ESCALATED_TO_SUPPLIER = "ESCALATED_TO_SUPPLIER"
    RESOLVED = "RESOLVED"
    OVERRIDDEN = "OVERRIDDEN"


class ResolutionAction(str, enum.Enum):
    """Resolution action taken"""
    SUPPLIER_CORRECTION = "SUPPLIER_CORRECTION"
    USER_OVERRIDE = "USER_OVERRIDE"
    ESCALATED = "ESCALATED"
    PENDING = "PENDING"


class QuestionnaireIncident(Base):
    """Incident/alert for out-of-spec questionnaire responses"""
    __tablename__ = "questionnaire_incidents"

    id = Column(Integer, primary_key=True, index=True)
    questionnaire_id = Column(Integer, ForeignKey("questionnaires.id"), nullable=False, index=True)
    validation_id = Column(Integer, ForeignKey("questionnaire_validations.id"), nullable=True)
    
    # Incident details
    field_name = Column(String(200), nullable=False)
    issue_description = Column(Text, nullable=False)
    
    # Status
    status = Column(Enum(IncidentStatus), default=IncidentStatus.OPEN, index=True)
    resolution_action = Column(Enum(ResolutionAction), default=ResolutionAction.PENDING)
    
    # Assignment
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Resolution
    override_justification = Column(Text)
    resolution_notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    supplier_notified_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    
    # Relationships
    questionnaire = relationship("Questionnaire", back_populates="incidents")
    validation = relationship("QuestionnaireValidation", backref="incidents")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id], backref="assigned_incidents")
    created_by = relationship("User", foreign_keys=[created_by_id], backref="created_incidents")

    def __repr__(self):
        return f"<QuestionnaireIncident(id={self.id}, field={self.field_name}, status={self.status})>"

