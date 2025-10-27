from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Material(Base):
    """Material (raw material for fragrances and flavors)"""
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    reference_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    supplier = Column(String(200))
    description = Column(Text)
    cas_number = Column(String(50))
    material_type = Column(String(50))  # NATURAL, SYNTHETIC, etc.
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    composites = relationship("Composite", back_populates="material", cascade="all, delete-orphan")
    chromatographic_analyses = relationship("ChromatographicAnalysis", back_populates="material", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Material(id={self.id}, reference_code='{self.reference_code}', name='{self.name}')>"








