"""
Blue Line Logic Engine

Service that applies the Blue Line logic rules from CSV to create or update blue line specifications.
Takes questionnaire data and SAP data, applies appropriate logic rules to generate blue line.
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.questionnaire import Questionnaire
from app.models.blue_line import BlueLine, BlueLineMaterialType
from app.models.material import Material
from app.services.blue_line_rules import (
    LogicType,
    BLUE_LINE_FIELD_RULES,
    apply_sap_logic,
    apply_manual_logic,
    apply_concatenate_logic,
    apply_worst_case_logic,
    apply_blocked_logic,
    get_field_rule
)

logger = logging.getLogger(__name__)


class BlueLineLogicEngine:
    """
    Engine for applying Blue Line logic rules.
    Creates blue line specifications from questionnaires and SAP data.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_blue_line_from_questionnaire(
        self,
        material_id: int,
        questionnaire_id: int,
        material_type: BlueLineMaterialType = BlueLineMaterialType.Z001,
        sap_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create blue line responses from a questionnaire using logic rules.
        
        Args:
            material_id: Material ID
            questionnaire_id: Questionnaire ID to use as source
            material_type: Z001 or Z002
            sap_data: Optional SAP data dict
            
        Returns:
            Dict of responses in fieldCode format
        """
        # Get questionnaire
        questionnaire = self.db.query(Questionnaire).filter(
            Questionnaire.id == questionnaire_id
        ).first()
        
        if not questionnaire:
            raise ValueError(f"Questionnaire {questionnaire_id} not found")
        
        # Get material for SAP data if not provided
        material = self.db.query(Material).filter(Material.id == material_id).first()
        if not material:
            raise ValueError(f"Material {material_id} not found")
        
        # Use material data as SAP data if not provided
        if sap_data is None:
            sap_data = self._extract_sap_data_from_material(material)
        
        # Apply logic rules
        if material_type == BlueLineMaterialType.Z001:
            responses = self._apply_z001_logic(questionnaire, sap_data)
        else:
            responses = self._apply_z002_logic(questionnaire, sap_data)
        
        logger.info(
            f"Created blue line responses for material {material_id} "
            f"from questionnaire {questionnaire_id} with {len(responses)} fields"
        )
        
        return responses
    
    def _extract_sap_data_from_material(self, material: Material) -> Dict[str, Any]:
        """Extract SAP-like data from Material model"""
        return {
            "material_name": material.name,
            "material_reference": material.reference_code,
            "cas_number": material.cas_number,
            # Add more mappings as needed
        }
    
    def _apply_z001_logic(
        self,
        questionnaire: Questionnaire,
        sap_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply Z001 (provisional, worst case) logic.
        
        For Z001:
        - SAP fields: use SAP data
        - Concatenate fields: combine all supplier values
        - Worst case fields: apply worst case hierarchy
        - Manual fields: leave empty
        - Blocked fields: block
        
        Args:
            questionnaire: Source questionnaire
            sap_data: SAP data dict
            
        Returns:
            Blue line responses dict
        """
        responses = {}
        questionnaire_responses = questionnaire.responses or {}
        
        # Process each field according to its rule
        for field_code, rule in BLUE_LINE_FIELD_RULES.items():
            logic_type = rule.get("logic_z001")
            blue_line_field = rule.get("blue_line_field")
            
            if logic_type == LogicType.SAP:
                # Use SAP data
                value = sap_data.get(blue_line_field)
                if value:
                    responses[field_code] = {
                        "value": value,
                        "name": blue_line_field,
                        "type": "text",
                        "source": "SAP"
                    }
            
            elif logic_type == LogicType.CONCATENATE:
                # For Z001, concatenate all available supplier values
                # In real implementation, this would query all suppliers for this material
                q_value = self._extract_field_value(questionnaire_responses, field_code)
                if q_value:
                    concat_value = apply_concatenate_logic([q_value])
                    responses[field_code] = {
                        "value": concat_value,
                        "name": blue_line_field,
                        "type": "text",
                        "source": "CONCATENATED"
                    }
            
            elif logic_type == LogicType.WORST_CASE:
                # Apply worst case logic
                hierarchy = rule.get("worst_case")
                q_value = self._extract_field_value(questionnaire_responses, field_code)
                
                # In real implementation, get values from all suppliers
                # For now, use single questionnaire value
                values = [q_value] if q_value else []
                
                if values:
                    worst_value = apply_worst_case_logic(values, hierarchy)
                    responses[field_code] = {
                        "value": worst_value,
                        "name": blue_line_field,
                        "type": "lov",
                        "source": "WORST_CASE"
                    }
            
            elif logic_type == LogicType.MANUAL:
                # Leave empty for manual entry
                responses[field_code] = {
                    "value": None,
                    "name": blue_line_field,
                    "type": "text",
                    "source": "MANUAL"
                }
            
            elif logic_type == LogicType.BLOCKED:
                # Blocked field
                responses[field_code] = {
                    "value": "",
                    "name": blue_line_field,
                    "type": "text",
                    "source": "BLOCKED",
                    "editable": False
                }
        
        return responses
    
    def _apply_z002_logic(
        self,
        questionnaire: Questionnaire,
        sap_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply Z002 (definitive, from Lluch analysis) logic.
        
        For Z002:
        - Most fields are MANUAL (filled by technical/regulatory team)
        - SAP fields still use SAP data
        - Less reliance on supplier questionnaire
        
        Args:
            questionnaire: Source questionnaire (used minimally)
            sap_data: SAP data dict
            
        Returns:
            Blue line responses dict
        """
        responses = {}
        
        # Process each field according to its Z002 rule
        for field_code, rule in BLUE_LINE_FIELD_RULES.items():
            logic_type = rule.get("logic_z002")
            blue_line_field = rule.get("blue_line_field")
            
            if logic_type == LogicType.SAP:
                # Still use SAP data for Z002
                value = sap_data.get(blue_line_field)
                if value:
                    responses[field_code] = {
                        "value": value,
                        "name": blue_line_field,
                        "type": "text",
                        "source": "SAP"
                    }
            
            elif logic_type == LogicType.MANUAL:
                # Most fields are manual for Z002
                responses[field_code] = {
                    "value": None,
                    "name": blue_line_field,
                    "type": "text",
                    "source": "MANUAL_Z002"
                }
            
            elif logic_type == LogicType.BLOCKED:
                # Blocked field
                responses[field_code] = {
                    "value": "",
                    "name": blue_line_field,
                    "type": "text",
                    "source": "BLOCKED",
                    "editable": False
                }
        
        return responses
    
    def _extract_field_value(self, responses: Dict[str, Any], field_code: str) -> Any:
        """Extract value from questionnaire response field"""
        field_data = responses.get(field_code)
        if not field_data:
            return None
        
        if isinstance(field_data, dict):
            return field_data.get("value")
        return field_data
    
    def merge_supplier_data_for_z001(
        self,
        material_id: int,
        questionnaire_ids: List[int]
    ) -> Dict[str, Any]:
        """
        Merge data from multiple supplier questionnaires for Z001.
        Applies concatenation and worst-case logic across all suppliers.
        
        Args:
            material_id: Material ID
            questionnaire_ids: List of questionnaire IDs to merge
            
        Returns:
            Merged blue line responses
        """
        # Get all questionnaires
        questionnaires = self.db.query(Questionnaire).filter(
            Questionnaire.id.in_(questionnaire_ids),
            Questionnaire.material_id == material_id
        ).all()
        
        if not questionnaires:
            raise ValueError("No questionnaires found")
        
        merged_responses = {}
        
        # For each field, collect values from all suppliers
        for field_code, rule in BLUE_LINE_FIELD_RULES.items():
            logic_type = rule.get("logic_z001")
            blue_line_field = rule.get("blue_line_field")
            
            if logic_type == LogicType.CONCATENATE:
                # Collect all values
                values = []
                for q in questionnaires:
                    val = self._extract_field_value(q.responses or {}, field_code)
                    if val:
                        values.append(val)
                
                if values:
                    merged_value = apply_concatenate_logic(values)
                    merged_responses[field_code] = {
                        "value": merged_value,
                        "name": blue_line_field,
                        "type": "text",
                        "source": "CONCATENATED"
                    }
            
            elif logic_type == LogicType.WORST_CASE:
                # Collect all values and apply worst case
                hierarchy = rule.get("worst_case")
                values = []
                for q in questionnaires:
                    val = self._extract_field_value(q.responses or {}, field_code)
                    if val:
                        values.append(val)
                
                if values:
                    worst_value = apply_worst_case_logic(values, hierarchy)
                    merged_responses[field_code] = {
                        "value": worst_value,
                        "name": blue_line_field,
                        "type": "lov",
                        "source": "WORST_CASE"
                    }
        
        return merged_responses



