from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class MaterialSupplierStatus(str, enum.Enum):
    """Material-Supplier status"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class MaterialSupplier(Base):
    """
    Material-Supplier relationship
    
    Represents a validated material-supplier pairing with a questionnaire.
    This is created when a questionnaire is accepted and validated against a Blue Line.
    """
    __tablename__ = "material_suppliers"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False, index=True)
    questionnaire_id = Column(Integer, ForeignKey("questionnaires.id"), nullable=False, unique=True, index=True)
    blue_line_id = Column(Integer, ForeignKey("blue_lines.id"), nullable=True, index=True)
    
    # Supplier information
    supplier_code = Column(String(100), nullable=False, index=True)
    supplier_name = Column(String(200), nullable=True)
    
    # Validation results
    status = Column(Enum(MaterialSupplierStatus), default=MaterialSupplierStatus.ACTIVE, index=True)
    validation_score = Column(Integer, default=0)  # 0-100 score based on comparison
    
    # Comparison details
    mismatch_fields = Column(JSON, default=list)  # List of mismatched fields with details
    accepted_mismatches = Column(JSON, default=list)  # List of fieldCodes that were accepted despite mismatch
    
    # Timestamps
    validated_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    material = relationship("Material", backref="material_suppliers")
    questionnaire = relationship("Questionnaire", backref="material_supplier", uselist=False)
    blue_line = relationship("BlueLine", foreign_keys=[blue_line_id], backref="material_suppliers")

    def __repr__(self):
        return f"<MaterialSupplier(id={self.id}, material_id={self.material_id}, supplier_code={self.supplier_code}, score={self.validation_score})>"

