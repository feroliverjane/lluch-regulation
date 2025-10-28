"""
Questionnaire CSV Parser

Parses questionnaire CSV files submitted by suppliers and loads them into the system.
"""

import csv
from typing import Dict, Any, Tuple
from datetime import datetime
from pathlib import Path


class QuestionnaireCSVParser:
    """Parser for supplier questionnaire CSV files"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.metadata = {}
        self.responses = {}
        self.changes_explanation = []
    
    def parse(self) -> Dict[str, Any]:
        """
        Parse the CSV file and extract questionnaire data.
        
        Returns:
            {
                "metadata": {...},
                "responses": {...},
                "changes_explanation": [...]
            }
        """
        with open(self.file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        current_section = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Detect section headers
            if line.startswith('SECCIÓN') or line.startswith('CUESTIONARIO'):
                current_section = line
                continue
            
            # Parse metadata (first lines)
            if i < 10 and ',' in line:
                parts = [p.strip() for p in line.split(',', 1)]
                if len(parts) == 2:
                    key, value = parts
                    if key in ['Material', 'Nombre Material', 'Código Proveedor', 'Fecha Envío', 'Versión', 'Versión Anterior', 'Motivo Rehomologación']:
                        self.metadata[key] = value
                continue
            
            # Skip header rows
            if line.startswith('Campo,Valor') or line.startswith('Cambio,Explicación'):
                continue
            
            # Parse responses
            if current_section and ',' in line:
                parts = [p.strip() for p in line.split(',', 2)]
                
                if len(parts) >= 2:
                    field, value = parts[0], parts[1]
                    
                    # Skip section title rows
                    if field.upper() == field and len(field) > 20:
                        continue
                    
                    # Store response
                    if field and value and field not in ['Campo', 'Cambio']:
                        self.responses[field] = value
                    
                    # Store change explanations if present
                    if 'EXPLICACIÓN DE CAMBIOS' in (current_section or ''):
                        if len(parts) == 3 and field and value:
                            self.changes_explanation.append({
                                "field": field,
                                "explanation": value,
                                "corrective_action": parts[2] if len(parts) > 2 else ""
                            })
        
        return {
            "metadata": self.metadata,
            "responses": self.responses,
            "changes_explanation": self.changes_explanation
        }
    
    def extract_questionnaire_data(self) -> Tuple[str, str, str, int, Dict[str, Any]]:
        """
        Extract data in format ready for Questionnaire model.
        
        Returns:
            (material_code, supplier_code, questionnaire_type, version, responses)
        """
        parsed = self.parse()
        
        material_code = parsed["metadata"].get("Material", "")
        supplier_code = parsed["metadata"].get("Código Proveedor", "")
        version = int(parsed["metadata"].get("Versión", "1"))
        
        # Determine type
        if "Versión Anterior" in parsed["metadata"]:
            questionnaire_type = "REHOMOLOGATION"
        else:
            questionnaire_type = "INITIAL_HOMOLOGATION"
        
        # Add metadata to responses
        responses = parsed["responses"].copy()
        responses["_metadata"] = {
            "submission_date": parsed["metadata"].get("Fecha Envío", ""),
            "previous_version": parsed["metadata"].get("Versión Anterior", ""),
            "rehomologation_reason": parsed["metadata"].get("Motivo Rehomologación", ""),
            "changes_explanation": parsed.get("changes_explanation", [])
        }
        
        return material_code, supplier_code, questionnaire_type, version, responses
    
    @staticmethod
    def import_from_csv(file_path: str, db) -> int:
        """
        Import a questionnaire from CSV file into the database.
        
        Args:
            file_path: Path to CSV file
            db: Database session
            
        Returns:
            questionnaire_id: ID of created questionnaire
        """
        from app.models.material import Material
        from app.models.questionnaire import Questionnaire, QuestionnaireType
        
        parser = QuestionnaireCSVParser(file_path)
        material_code, supplier_code, q_type, version, responses = parser.extract_questionnaire_data()
        
        # Find material
        material = db.query(Material).filter(
            Material.reference_code == material_code
        ).first()
        
        if not material:
            raise ValueError(f"Material {material_code} not found in database")
        
        # Check for previous version if rehomologation
        previous_version_id = None
        if q_type == "REHOMOLOGATION":
            previous = db.query(Questionnaire).filter(
                Questionnaire.material_id == material.id,
                Questionnaire.supplier_code == supplier_code
            ).order_by(Questionnaire.version.desc()).first()
            
            if previous:
                previous_version_id = previous.id
        
        # Create questionnaire
        questionnaire = Questionnaire(
            material_id=material.id,
            supplier_code=supplier_code,
            questionnaire_type=QuestionnaireType[q_type],
            version=version,
            previous_version_id=previous_version_id,
            responses=responses
        )
        
        db.add(questionnaire)
        db.commit()
        db.refresh(questionnaire)
        
        return questionnaire.id


def parse_questionnaire_csv(file_path: str) -> Dict[str, Any]:
    """
    Convenience function to parse a questionnaire CSV.
    
    Args:
        file_path: Path to CSV file
        
    Returns:
        Parsed questionnaire data
    """
    parser = QuestionnaireCSVParser(file_path)
    return parser.parse()

