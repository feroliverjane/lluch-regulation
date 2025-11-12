"""
Questionnaire JSON Parser

Parses questionnaire JSON files in the real Lluch format with fieldCode structure.
Format: { "requestId": X, "data": [ { "fieldCode": "...", "fieldName": "...", "fieldType": "...", "value": "..." } ] }
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path


class QuestionnaireJSONParser:
    """Parser for Lluch questionnaire JSON format"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.raw_data = None
        self.request_id = None
        self.fields = []
    
    def parse(self) -> Dict[str, Any]:
        """
        Parse the JSON file and extract questionnaire data.
        
        Returns:
            {
                "request_id": int,
                "fields": [...],
                "responses": {...},
                "metadata": {...}
            }
        """
        with open(self.file_path, 'r', encoding='utf-8') as file:
            self.raw_data = json.load(file)
        
        self.request_id = self.raw_data.get("requestId")
        self.fields = self.raw_data.get("data", [])
        
        # Extract responses and metadata
        responses = {}
        metadata = {
            "request_id": self.request_id,
            "total_fields": len(self.fields),
            "field_types": {}
        }
        
        # Extract key metadata fields
        supplier_name = None
        product_name = None
        product_code = None
        
        for field in self.fields:
            field_code = field.get("fieldCode", "")
            field_name = field.get("fieldName", "")
            field_type = field.get("fieldType", "")
            value = field.get("value", "")
            
            # Skip blank fields
            if field_type == "blank" or not field_name.strip():
                continue
            
            # Store response with fieldCode as key for traceability
            responses[field_code] = {
                "name": field_name,
                "type": field_type,
                "value": value
            }
            
            # Track field types
            metadata["field_types"][field_type] = metadata["field_types"].get(field_type, 0) + 1
            
            # Extract key metadata
            if "Supplier Name" in field_name or "Supplier´s name" in field_name:
                supplier_name = value
            elif "Product Name" in field_name:
                product_name = value
            elif "product code" in field_name.lower():
                product_code = value
        
        if supplier_name:
            metadata["supplier_name"] = supplier_name
        if product_name:
            metadata["product_name"] = product_name
        if product_code:
            metadata["product_code"] = product_code
        
        return {
            "request_id": self.request_id,
            "fields": self.fields,
            "responses": responses,
            "metadata": metadata
        }
    
    def extract_by_section(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Organize fields by section (extracted from fieldCode).
        
        fieldCode format: q{questionnaire}t{tab}s{section}f{field}
        Example: q3t1s2f15 = questionnaire 3, tab 1, section 2, field 15
        """
        if not self.fields:
            self.parse()
        
        sections = {}
        
        for field in self.fields:
            field_code = field.get("fieldCode", "")
            
            # Skip blank fields
            if field.get("fieldType") == "blank" or not field.get("fieldName", "").strip():
                continue
            
            # Extract section from fieldCode (e.g., q3t1s2f15 -> section 2)
            try:
                if 's' in field_code:
                    section_part = field_code.split('s')[1].split('f')[0]
                    section_key = f"Section_{section_part}"
                else:
                    section_key = "General"
            except:
                section_key = "General"
            
            if section_key not in sections:
                sections[section_key] = []
            
            sections[section_key].append(field)
        
        return sections
    
    def get_critical_fields(self) -> Dict[str, Any]:
        """Extract the most important fields for Blue Line comparison"""
        if not self.fields:
            self.parse()
        
        critical_fields = {}
        
        # Define critical field patterns
        critical_patterns = {
            "supplier_name": ["Supplier Name", "Supplier´s name"],
            "product_name": ["Product Name"],
            "product_code": ["product code", "Supplier´s product code"],
            "cas_number": ["CAS"],
            "einecs_number": ["EINECS"],  # Optional but important for EU materials
            "botanical_name": ["Botanical name"],
            "country_origin": ["Country of the botanical origin"],
            "natural_product": ["Is the product 100% Natural"],
            "pure_product": ["Is the product 100% Pure"],
            "kosher": ["KOSHER CERTIFICATE"],
            "halal": ["HALAL CERTIFICATE"],
            "food_grade": ["FOOD/FLAVOUR GRADE"],
            "shelf_life": ["shelf life"],
            "storage_temp": ["storage temperature", "transport temperature"],
        }
        
        for key, patterns in critical_patterns.items():
            for field in self.fields:
                field_name = field.get("fieldName", "")
                for pattern in patterns:
                    if pattern.lower() in field_name.lower():
                        critical_fields[key] = {
                            "field_code": field.get("fieldCode"),
                            "field_name": field_name,
                            "value": field.get("value"),
                            "type": field.get("fieldType")
                        }
                        break
                if key in critical_fields:
                    break
        
        return critical_fields
    
    @staticmethod
    def import_from_json(file_path: str, db, material_code: str = None) -> int:
        """
        Import a questionnaire from JSON file into the database.
        
        Args:
            file_path: Path to JSON file
            db: Database session
            material_code: Material code (if not in JSON, must be provided)
            
        Returns:
            questionnaire_id: ID of created questionnaire
        """
        from app.models.material import Material
        from app.models.questionnaire import Questionnaire, QuestionnaireType
        
        parser = QuestionnaireJSONParser(file_path)
        parsed_data = parser.parse()
        
        # Extract metadata
        metadata = parsed_data["metadata"]
        responses = parsed_data["responses"]
        
        # Determine material
        if not material_code:
            # Try to extract from product code in JSON
            material_code = metadata.get("product_code", "")
            if material_code and material_code.startswith("[") and "]" in material_code:
                # Extract code from format: [BASIL0003] H.E. BASILIC INDES
                material_code = material_code.split("]")[0].replace("[", "")
        
        if not material_code:
            raise ValueError("Material code not found in JSON and not provided")
        
        # Find or create material
        material = db.query(Material).filter(
            Material.reference_code == material_code
        ).first()
        
        if not material:
            raise ValueError(f"Material {material_code} not found in database. Create material first.")
        
        # Extract supplier code
        supplier_code = metadata.get("supplier_name", "SUPPLIER-UNKNOWN")[:100]
        
        # Determine questionnaire type (assume initial if no previous version)
        questionnaire_type = QuestionnaireType.INITIAL_HOMOLOGATION
        
        # Check for existing questionnaires to determine version
        existing_count = db.query(Questionnaire).filter(
            Questionnaire.material_id == material.id,
            Questionnaire.supplier_code == supplier_code
        ).count()
        
        version = existing_count + 1
        previous_version_id = None
        
        if version > 1:
            questionnaire_type = QuestionnaireType.REHOMOLOGATION
            previous = db.query(Questionnaire).filter(
                Questionnaire.material_id == material.id,
                Questionnaire.supplier_code == supplier_code
            ).order_by(Questionnaire.version.desc()).first()
            
            if previous:
                previous_version_id = previous.id
        
        # Create questionnaire with full JSON structure preserved
        questionnaire = Questionnaire(
            material_id=material.id,
            supplier_code=supplier_code,
            questionnaire_type=questionnaire_type,
            version=version,
            previous_version_id=previous_version_id,
            responses={
                **responses,  # All field responses
                "_metadata": metadata,  # Preserve metadata
                "_request_id": parsed_data["request_id"]  # Original request ID
            }
        )
        
        db.add(questionnaire)
        db.commit()
        db.refresh(questionnaire)
        
        return questionnaire.id
    
    def convert_to_csv(self, output_path: str) -> None:
        """Convert JSON questionnaire to CSV format"""
        import csv
        
        if not self.fields:
            self.parse()
        
        with open(output_path, 'w', encoding='utf-8', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['Field Code', 'Field Name', 'Field Type', 'Value'])
            
            # Write data
            for field in self.fields:
                if field.get("fieldType") != "blank":
                    writer.writerow([
                        field.get("fieldCode", ""),
                        field.get("fieldName", ""),
                        field.get("fieldType", ""),
                        field.get("value", "")
                    ])


def parse_questionnaire_json(file_path: str) -> Dict[str, Any]:
    """
    Convenience function to parse a questionnaire JSON.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Parsed questionnaire data
    """
    parser = QuestionnaireJSONParser(file_path)
    return parser.parse()

