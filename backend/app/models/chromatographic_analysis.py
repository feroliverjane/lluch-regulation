from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ChromatographicAnalysis(Base):
    """Chromatographic analysis data"""
    __tablename__ = "chromatographic_analyses"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    
    # File information
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    
    # Analysis details
    batch_number = Column(String(100))
    supplier = Column(String(200))
    analysis_date = Column(DateTime(timezone=True))
    lab_technician = Column(String(200))
    
    # Parsed data stored as JSON
    parsed_data = Column(JSON)  # List of {cas, component, percentage, type}
    
    # Processing metadata
    is_processed = Column(Integer, default=0)  # 0: not processed, 1: processed, -1: error
    processing_notes = Column(Text)
    
    # Weight for aggregation (batch size or quantity)
    weight = Column(Float, default=1.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    material = relationship("Material", back_populates="chromatographic_analyses")

    def __repr__(self):
        return f"<ChromatographicAnalysis(id={self.id}, material_id={self.material_id}, filename='{self.filename}')>"








