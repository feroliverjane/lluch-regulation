from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class TemplateType(str, enum.Enum):
    """Type of questionnaire template"""
    INITIAL_HOMOLOGATION = "INITIAL_HOMOLOGATION"
    REHOMOLOGATION = "REHOMOLOGATION"


class QuestionnaireTemplate(Base):
    """Template defining questionnaire structure and questions"""
    __tablename__ = "questionnaire_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    template_type = Column(Enum(TemplateType), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    
    # Questions schema - array of question definitions
    # Structure: [{"fieldCode": "q3t1s2f15", "fieldName": "...", "fieldType": "...", "section": "...", "required": bool, ...}]
    questions_schema = Column(JSON, nullable=False)
    
    # Scoring rules (optional)
    scoring_rules = Column(JSON)
    
    # Metadata
    total_questions = Column(Integer)
    total_sections = Column(Integer)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<QuestionnaireTemplate(id={self.id}, name='{self.name}', type={self.template_type}, version={self.version})>"

