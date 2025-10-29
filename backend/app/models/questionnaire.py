from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class QuestionnaireType(str, enum.Enum):
    """Type of questionnaire"""
    INITIAL_HOMOLOGATION = "INITIAL_HOMOLOGATION"
    REHOMOLOGATION = "REHOMOLOGATION"


class QuestionnaireStatus(str, enum.Enum):
    """Questionnaire status"""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REQUIRES_REVISION = "REQUIRES_REVISION"


class Questionnaire(Base):
    """Questionnaire for material-supplier homologation"""
    __tablename__ = "questionnaires"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False, index=True)
    supplier_code = Column(String(100), nullable=False, index=True)
    
    # Template reference (optional - for structured questionnaires)
    template_id = Column(Integer, ForeignKey("questionnaire_templates.id"), nullable=True, index=True)
    
    # Type and versioning
    questionnaire_type = Column(Enum(QuestionnaireType), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    previous_version_id = Column(Integer, ForeignKey("questionnaires.id"), nullable=True)
    
    # Data
    responses = Column(JSON, default=dict)  # {question_id: answer_value}
    
    # Status
    status = Column(Enum(QuestionnaireStatus), default=QuestionnaireStatus.DRAFT, index=True)
    
    # AI Analysis results
    ai_risk_score = Column(Integer)  # 0-100
    ai_summary = Column(Text)
    ai_recommendation = Column(String(50))  # "APPROVE", "REVIEW", "REJECT"
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    submitted_at = Column(DateTime(timezone=True))
    reviewed_at = Column(DateTime(timezone=True))
    approved_at = Column(DateTime(timezone=True))
    
    # Relationships
    material = relationship("Material", backref="questionnaires")
    template = relationship("QuestionnaireTemplate", backref="questionnaires")
    previous_version = relationship("Questionnaire", remote_side=[id], foreign_keys=[previous_version_id])
    validations = relationship("QuestionnaireValidation", back_populates="questionnaire", cascade="all, delete-orphan")
    incidents = relationship("QuestionnaireIncident", back_populates="questionnaire", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Questionnaire(id={self.id}, material_id={self.material_id}, version={self.version}, status={self.status})>"

