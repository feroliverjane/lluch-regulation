from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class BlueLineMaterialType(str, enum.Enum):
    """Blue Line material type based on homologation status"""
    Z001 = "Z001"  # Provisional estimated (worst case from supplier)
    Z002 = "Z002"  # Homologated (data from Lluch analysis)


class BlueLineSyncStatus(str, enum.Enum):
    """Synchronization status with SAP"""
    PENDING = "PENDING"
    SYNCED = "SYNCED"
    FAILED = "FAILED"
    NOT_REQUIRED = "NOT_REQUIRED"


class BlueLine(Base):
    """
    Blue Line (Línea Azul) - LLUCH material-supplier homologation record
    Represents the internal homologation specification for a material-supplier pair
    """
    __tablename__ = "blue_lines"
    
    __table_args__ = (
        UniqueConstraint('material_id', 'supplier_code', name='uq_material_supplier'),
    )

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False, index=True)
    supplier_code = Column(String(100), nullable=False, index=True)
    
    # Blue Line data - 446 configurable fields stored as JSON
    blue_line_data = Column(JSON, default=dict)
    
    # Material type classification
    material_type = Column(Enum(BlueLineMaterialType), nullable=False)
    
    # Synchronization tracking
    sync_status = Column(Enum(BlueLineSyncStatus), default=BlueLineSyncStatus.PENDING)
    last_synced_at = Column(DateTime(timezone=True))
    sync_error_message = Column(String(500))
    
    # Metadata about calculation (renamed to avoid SQLAlchemy reserved word)
    bl_metadata = Column("metadata", JSON, default=dict)  # Calculation details, applied logic rules, source data
    
    # Timestamps
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    material = relationship("Material", back_populates="blue_lines")

    def __repr__(self):
        return f"<BlueLine(id={self.id}, material_id={self.material_id}, supplier_code='{self.supplier_code}', type={self.material_type})>"

