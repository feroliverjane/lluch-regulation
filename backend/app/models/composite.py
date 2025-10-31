from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class CompositeOrigin(str, enum.Enum):
    """Origin of composite data"""
    LAB = "LAB"  # From chromatographic analysis
    CALCULATED = "CALCULATED"  # Calculated from documents
    MANUAL = "MANUAL"  # Manually entered


class CompositeStatus(str, enum.Enum):
    """Status of composite"""
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"


class ComponentType(str, enum.Enum):
    """Type of component"""
    COMPONENT = "COMPONENT"  # Main component
    IMPURITY = "IMPURITY"  # Impurity


class CompositeType(str, enum.Enum):
    """Type of composite based on source"""
    Z1 = "Z1"  # Generated from supplier documents (provisional)
    Z2 = "Z2"  # From laboratory analysis (final, definitive)


class Composite(Base):
    """Composite table describing material composition"""
    __tablename__ = "composites"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    version = Column(Integer, nullable=False)
    origin = Column(Enum(CompositeOrigin), nullable=False)
    status = Column(Enum(CompositeStatus), default=CompositeStatus.DRAFT)
    
    # Composite type (Z1 from documents, Z2 from lab)
    composite_type = Column(Enum(CompositeType), nullable=True, index=True)
    
    # Link to questionnaire for material-supplier specific composites
    questionnaire_id = Column(Integer, ForeignKey("questionnaires.id"), nullable=True, index=True)
    
    # Document tracking for Z1 composites
    source_documents = Column(JSON)  # [{filename: str, path: str, upload_date: str}]
    
    # AI extraction confidence for Z1 composites
    extraction_confidence = Column(Float)  # 0-100 score
    
    # Metadata as JSON (renamed from metadata to avoid SQLAlchemy reserved word)
    composite_metadata = Column(JSON)  # {batches: [], suppliers: [], purchase_dates: [], analysis_ids: []}
    
    # Notes
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    approved_at = Column(DateTime(timezone=True))
    
    # Relationships
    material = relationship("Material", back_populates="composites")
    components = relationship("CompositeComponent", back_populates="composite", cascade="all, delete-orphan")
    workflow = relationship("ApprovalWorkflow", back_populates="composite", uselist=False, cascade="all, delete-orphan")
    questionnaire = relationship("Questionnaire", foreign_keys=[questionnaire_id], backref="composites")

    def __repr__(self):
        return f"<Composite(id={self.id}, material_id={self.material_id}, version={self.version}, status={self.status})>"


class CompositeComponent(Base):
    """Individual component in a composite"""
    __tablename__ = "composite_components"

    id = Column(Integer, primary_key=True, index=True)
    composite_id = Column(Integer, ForeignKey("composites.id"), nullable=False)
    
    cas_number = Column(String(50))
    component_name = Column(String(200), nullable=False)
    percentage = Column(Float, nullable=False)
    component_type = Column(Enum(ComponentType), default=ComponentType.COMPONENT)
    
    # Additional info
    confidence_level = Column(Float)  # 0-100, for LAB origin
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    composite = relationship("Composite", back_populates="components")

    def __repr__(self):
        return f"<CompositeComponent(id={self.id}, name='{self.component_name}', percentage={self.percentage}%)>"

