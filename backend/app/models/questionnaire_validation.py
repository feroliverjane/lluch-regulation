from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, JSON, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class ValidationType(str, enum.Enum):
    """Type of validation"""
    BLUE_LINE_COMPARISON = "BLUE_LINE_COMPARISON"
    VERSION_COMPARISON = "VERSION_COMPARISON"
    AI_RISK_ASSESSMENT = "AI_RISK_ASSESSMENT"


class ValidationSeverity(str, enum.Enum):
    """Severity of validation issue"""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class QuestionnaireValidation(Base):
    """Validation results for questionnaire responses"""
    __tablename__ = "questionnaire_validations"

    id = Column(Integer, primary_key=True, index=True)
    questionnaire_id = Column(Integer, ForeignKey("questionnaires.id"), nullable=False, index=True)
    
    # Validation details
    validation_type = Column(Enum(ValidationType), nullable=False)
    field_name = Column(String(200), nullable=False)
    
    # Values
    expected_value = Column(String(500))
    actual_value = Column(String(500))
    deviation_percentage = Column(Float)
    
    # Severity and action
    severity = Column(Enum(ValidationSeverity), nullable=False)
    requires_action = Column(Boolean, default=False)
    
    # AI analysis
    ai_analysis = Column(JSON)  # AI-generated insights about this field
    message = Column(Text)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    questionnaire = relationship("Questionnaire", back_populates="validations")

    def __repr__(self):
        return f"<QuestionnaireValidation(id={self.id}, field={self.field_name}, severity={self.severity})>"

