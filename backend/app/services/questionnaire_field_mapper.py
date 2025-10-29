"""
Questionnaire Field Mapper

Maps between Lluch fieldCodes and Blue Line fields for validation.
This allows the system to compare questionnaire responses with Blue Line expected values.
"""

from typing import Dict, Any, Optional, List


class QuestionnaireFieldMapper:
    """Maps questionnaire fieldCodes to Blue Line fields"""
    
    # Mapping of fieldCodes to Blue Line field names and validation rules
    FIELD_MAPPINGS = {
        # Basic Product Information
        "q3t1s2f15": {
            "blue_line_field": "supplier_name",
            "field_name": "Supplier Name",
            "critical": True,
            "validation": "exact_match"
        },
        "q3t1s2f16": {
            "blue_line_field": "material_name",
            "field_name": "Product Name",
            "critical": True,
            "validation": "exact_match"
        },
        "q3t1s2f17": {
            "blue_line_field": "material_reference",
            "field_name": "Product Code",
            "critical": True,
            "validation": "exact_match"
        },
        "q3t1s2f23": {
            "blue_line_field": "cas_number",
            "field_name": "CAS Number",
            "critical": True,
            "validation": "exact_match"
        },
        
        # Certifications (Critical for compliance)
        "q3t1s3f27": {
            "blue_line_field": "kosher_certified",
            "field_name": "Kosher Certificate",
            "critical": True,
            "validation": "boolean"
        },
        "q3t1s3f28": {
            "blue_line_field": "halal_certified",
            "field_name": "Halal Certificate",
            "critical": True,
            "validation": "boolean"
        },
        "q3t1s3f29": {
            "blue_line_field": "food_grade",
            "field_name": "Food/Flavour Grade",
            "critical": True,
            "validation": "boolean"
        },
        
        # Origin and Source
        "q3t1s4f33": {
            "blue_line_field": "country_origin",
            "field_name": "Country of Botanical Origin",
            "critical": True,
            "validation": "exact_match"
        },
        "q3t1s4f38": {
            "blue_line_field": "botanical_name",
            "field_name": "Botanical Name",
            "critical": True,
            "validation": "exact_match"
        },
        
        # Quality Parameters
        "q3t1s4f44": {
            "blue_line_field": "is_natural",
            "field_name": "100% Natural",
            "critical": True,
            "validation": "boolean"
        },
        "q3t1s4f46": {
            "blue_line_field": "is_pure",
            "field_name": "100% Pure",
            "critical": True,
            "validation": "boolean"
        },
        
        # Storage
        "q3t1s40f347": {
            "blue_line_field": "shelf_life",
            "field_name": "Shelf Life",
            "critical": False,
            "validation": "text"
        },
        "q3t1s40f348": {
            "blue_line_field": "storage_temperature",
            "field_name": "Storage Temperature",
            "critical": False,
            "validation": "text"
        },
        
        # Sustainability
        "q3t8s38f308": {
            "blue_line_field": "renewability_percentage",
            "field_name": "Renewability Percentage",
            "critical": False,
            "validation": "numeric",
            "threshold_warning": 5.0,
            "threshold_critical": 10.0
        },
        
        # REACH and Regulatory
        "q3t3s6f172": {
            "blue_line_field": "reach_registered",
            "field_name": "REACH Registered",
            "critical": True,
            "validation": "boolean"
        },
        "q3t3s20f188": {
            "blue_line_field": "cosmetics_compliant",
            "field_name": "Cosmetics Regulation Compliant",
            "critical": True,
            "validation": "boolean"
        },
        
        # Food Safety
        "q3t4s25f228": {
            "blue_line_field": "haccp_certified",
            "field_name": "HACCP Certificate",
            "critical": True,
            "validation": "boolean"
        },
        "q3t4s27f242": {
            "blue_line_field": "eu_compliant",
            "field_name": "EU Regulations Compliant",
            "critical": True,
            "validation": "boolean"
        },
        
        # Allergen Control
        "q3t4s32f265": {
            "blue_line_field": "allergen_control_plan",
            "field_name": "Allergen Control Plan",
            "critical": True,
            "validation": "boolean"
        },
        "q3t4s32f267": {
            "blue_line_field": "allergen_traces",
            "field_name": "May Contain Traces",
            "critical": True,
            "validation": "text"
        },
        
        # Animal Origin
        "q3t6s36f292": {
            "blue_line_field": "animal_origin",
            "field_name": "Animal Origin Ingredients",
            "critical": True,
            "validation": "boolean_inverted"  # NO is good
        },
    }
    
    @classmethod
    def get_blue_line_field(cls, field_code: str) -> Optional[str]:
        """Get the corresponding Blue Line field name for a fieldCode"""
        mapping = cls.FIELD_MAPPINGS.get(field_code)
        return mapping["blue_line_field"] if mapping else None
    
    @classmethod
    def is_critical_field(cls, field_code: str) -> bool:
        """Check if a field is critical for validation"""
        mapping = cls.FIELD_MAPPINGS.get(field_code)
        return mapping.get("critical", False) if mapping else False
    
    @classmethod
    def get_validation_type(cls, field_code: str) -> str:
        """Get the validation type for a field"""
        mapping = cls.FIELD_MAPPINGS.get(field_code)
        return mapping.get("validation", "text") if mapping else "text"
    
    @classmethod
    def get_field_name(cls, field_code: str) -> str:
        """Get the human-readable field name"""
        mapping = cls.FIELD_MAPPINGS.get(field_code)
        return mapping.get("field_name", field_code) if mapping else field_code
    
    @classmethod
    def get_all_critical_fields(cls) -> List[str]:
        """Get all critical fieldCodes"""
        return [code for code, mapping in cls.FIELD_MAPPINGS.items() if mapping.get("critical")]
    
    @classmethod
    def normalize_value(cls, field_code: str, value: Any) -> str:
        """Normalize value based on field type"""
        mapping = cls.FIELD_MAPPINGS.get(field_code)
        if not mapping:
            return str(value)
        
        validation_type = mapping.get("validation")
        
        # Handle boolean fields
        if validation_type in ["boolean", "boolean_inverted"]:
            # Convert various formats to YES/NO
            value_str = str(value).upper()
            if value_str in ["TRUE", "YES", "Y", "1", "SI", "SÍ"]:
                return "YES"
            elif value_str in ["FALSE", "NO", "N", "0"]:
                return "NO"
            elif value_str in ["NA", "N/A", "NOT APPLICABLE"]:
                return "NA"
        
        # Handle numeric fields
        elif validation_type == "numeric":
            try:
                return str(float(value))
            except:
                return str(value)
        
        return str(value).strip()
    
    @classmethod
    def extract_simple_value(cls, field_data: Dict[str, Any]) -> str:
        """
        Extract simple value from complex field data.
        
        Some fields have complex values like "YES|comment" or JSON arrays.
        This extracts the primary value.
        """
        if isinstance(field_data, dict):
            value = field_data.get("value", "")
        else:
            value = field_data
        
        value_str = str(value)
        
        # Handle "YES|comment" format
        if "|" in value_str:
            return value_str.split("|")[0].strip()
        
        # Handle JSON arrays/objects (for table fields)
        if value_str.startswith("[") or value_str.startswith("{"):
            try:
                import json
                parsed = json.loads(value_str)
                if isinstance(parsed, list) and len(parsed) > 0:
                    # For tables, check if any row has YES/contains data
                    for row in parsed:
                        if isinstance(row, dict):
                            if row.get("field2") == "YES":
                                return "YES"
                    return "NO"
                return "COMPLEX"
            except:
                pass
        
        return value_str.strip()


def map_questionnaire_to_blue_line(questionnaire_responses: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert questionnaire responses to Blue Line compatible format.
    
    Args:
        questionnaire_responses: Dict with fieldCode keys
        
    Returns:
        Dict with blue_line_field keys
    """
    blue_line_data = {}
    
    for field_code, field_data in questionnaire_responses.items():
        # Skip metadata fields
        if field_code.startswith("_"):
            continue
        
        # Get Blue Line field mapping
        bl_field = QuestionnaireFieldMapper.get_blue_line_field(field_code)
        
        if bl_field:
            # Extract and normalize value
            raw_value = field_data if isinstance(field_data, str) else field_data.get("value", "")
            simple_value = QuestionnaireFieldMapper.extract_simple_value(raw_value)
            normalized_value = QuestionnaireFieldMapper.normalize_value(field_code, simple_value)
            
            blue_line_data[bl_field] = normalized_value
    
    return blue_line_data

