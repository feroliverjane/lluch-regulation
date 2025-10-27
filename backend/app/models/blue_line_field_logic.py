from sqlalchemy import Column, Integer, String, Text, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy import DateTime
from app.core.database import Base


class BlueLineFieldLogic(Base):
    """
    Configuration for Blue Line field calculation logic
    Stores logic rules for each of the 446 Blue Line fields
    """
    __tablename__ = "blue_line_field_logics"

    id = Column(Integer, primary_key=True, index=True)
    
    # Field identification
    field_name = Column(String(200), unique=True, nullable=False, index=True)
    field_label = Column(String(500))  # Human-readable label
    field_category = Column(String(100), index=True)  # Grouping category (e.g., "Chemical Properties", "Regulatory")
    
    # Field type
    field_type = Column(String(50), nullable=False)  # "text", "number", "date", "boolean", "calculated", "selection"
    
    # Material type filter
    material_type_filter = Column(String(20), default="ALL")  # "Z001", "Z002", "ALL"
    
    # Logic configuration stored as JSON
    # Examples:
    # - {"source": "composite.component_name", "aggregation": "list"}
    # - {"source": "material.cas_number"}
    # - {"expression": "IF composite.origin == 'LAB' THEN composite.components ELSE []"}
    # - {"fixed_value": "LLUCH"}
    # - {"calculation": {"formula": "SUM(components.percentage WHERE component_type='IMPURITY')"}}
    logic_expression = Column(JSON, nullable=False)
    
    # Execution priority (lower numbers execute first)
    priority = Column(Integer, default=100)
    
    # Validation rules
    validation_rules = Column(JSON)  # {"required": true, "min": 0, "max": 100, "regex": "..."}
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Documentation
    description = Column(Text)
    example_value = Column(Text)
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<BlueLineFieldLogic(id={self.id}, field_name='{self.field_name}', type={self.field_type})>"

