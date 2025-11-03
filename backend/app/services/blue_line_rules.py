"""
Blue Line Rules

Helper functions and mappings for applying Blue Line logic rules from the CSV.
Maps questionnaire fieldCodes to Blue Line field names and defines logic rules.
"""

from typing import Dict, List, Any, Optional
from enum import Enum


class LogicType(str, Enum):
    """Type of logic to apply"""
    SAP = "SAP"  # Copy from SAP
    MANUAL = "MANUAL"  # Leave empty for manual entry
    CONCATENATE = "CONCATENATE"  # Combine multiple values
    WORST_CASE = "WORST_CASE"  # Apply worst case hierarchy
    BLOCKED = "BLOCKED"  # Not editable
    CALCULATED = "CALCULATED"  # Calculated field


class WorstCaseHierarchy(str, Enum):
    """Worst case hierarchies for boolean/trilean fields"""
    YES_NA_NO = "YES_NA_NO"  # Yes worst, NA middle, No best
    NO_NA_YES = "NO_NA_YES"  # No worst, NA middle, Yes best


# Mapping of fieldCodes to Blue Line rules
# Format: {fieldCode: {blue_line_field: str, logic_z001: LogicType, logic_z002: LogicType, worst_case: Optional[WorstCaseHierarchy]}}
BLUE_LINE_FIELD_RULES = {
    # Basic identifiers (SAP)
    "q3t1s2f15": {"blue_line_field": "supplier_name", "logic_z001": LogicType.SAP, "logic_z002": LogicType.SAP},
    "q3t1s2f16": {"blue_line_field": "material_name", "logic_z001": LogicType.SAP, "logic_z002": LogicType.SAP},
    "q3t1s2f17": {"blue_line_field": "material_reference", "logic_z001": LogicType.SAP, "logic_z002": LogicType.SAP},
    "q3t1s2f23": {"blue_line_field": "cas_number", "logic_z001": LogicType.SAP, "logic_z002": LogicType.SAP},
    "q3t1s2f24": {"blue_line_field": "einecs", "logic_z001": LogicType.SAP, "logic_z002": LogicType.SAP},
    "q3t1s2f25": {"blue_line_field": "fda_cfr_21", "logic_z001": LogicType.SAP, "logic_z002": LogicType.SAP},
    "q3t1s2f342": {"blue_line_field": "fema", "logic_z001": LogicType.SAP, "logic_z002": LogicType.SAP},
    "q3t1s2f343": {"blue_line_field": "jecfa", "logic_z001": LogicType.CONCATENATE, "logic_z002": LogicType.MANUAL},
    "q3t1s2f344": {"blue_line_field": "coe", "logic_z001": LogicType.CONCATENATE, "logic_z002": LogicType.MANUAL},
    "q3t1s2f345": {"blue_line_field": "flavis", "logic_z001": LogicType.CONCATENATE, "logic_z002": LogicType.MANUAL},
    
    # Origin and source
    "q3t1s4f33": {"blue_line_field": "country_origin", "logic_z001": LogicType.CONCATENATE, "logic_z002": LogicType.MANUAL},
    "q3t1s4f38": {"blue_line_field": "botanical_name", "logic_z001": LogicType.CONCATENATE, "logic_z002": LogicType.MANUAL},
    "q3t1s4f39": {"blue_line_field": "plant_part", "logic_z001": LogicType.CONCATENATE, "logic_z002": LogicType.MANUAL},
    
    # Natural and purity
    "q3t1s4f44": {"blue_line_field": "is_natural_100", "logic_z001": LogicType.WORST_CASE, "logic_z002": LogicType.MANUAL, "worst_case": WorstCaseHierarchy.NO_NA_YES},
    "q3t1s4f46": {"blue_line_field": "is_pure_100", "logic_z001": LogicType.WORST_CASE, "logic_z002": LogicType.MANUAL, "worst_case": WorstCaseHierarchy.NO_NA_YES},
    "q3t1s4f47": {"blue_line_field": "natural_reg_1334_2008", "logic_z001": LogicType.WORST_CASE, "logic_z002": LogicType.MANUAL, "worst_case": WorstCaseHierarchy.NO_NA_YES},
    "q3t1s4f48": {"blue_line_field": "natural_us_directive", "logic_z001": LogicType.WORST_CASE, "logic_z002": LogicType.MANUAL, "worst_case": WorstCaseHierarchy.NO_NA_YES},
    
    # RSPO
    "q3t1s4f54": {"blue_line_field": "rspo_member", "logic_z001": LogicType.WORST_CASE, "logic_z002": LogicType.MANUAL, "worst_case": WorstCaseHierarchy.NO_NA_YES},
    "q3t1s4f55": {"blue_line_field": "rspo_certified_product", "logic_z001": LogicType.WORST_CASE, "logic_z002": LogicType.MANUAL, "worst_case": WorstCaseHierarchy.NO_NA_YES},
    "q3t1s4f56": {"blue_line_field": "rspo_manufacturer", "logic_z001": LogicType.WORST_CASE, "logic_z002": LogicType.MANUAL, "worst_case": WorstCaseHierarchy.NO_NA_YES},
    
    # GMO and fermentation
    "q3t1s4f59": {"blue_line_field": "biocatalyst_gmo", "logic_z001": LogicType.WORST_CASE, "logic_z002": LogicType.MANUAL, "worst_case": WorstCaseHierarchy.YES_NA_NO},
    "q3t1s5f86": {"blue_line_field": "produced_with_gmo", "logic_z001": LogicType.WORST_CASE, "logic_z002": LogicType.MANUAL, "worst_case": WorstCaseHierarchy.YES_NA_NO},
    "q3t1s5f87": {"blue_line_field": "requires_gmo_label", "logic_z001": LogicType.WORST_CASE, "logic_z002": LogicType.MANUAL, "worst_case": WorstCaseHierarchy.YES_NA_NO},
    
    # General information (worst case = yes is worst)
    "q3t1s5f47": {"blue_line_field": "contains_additives", "logic_z001": LogicType.WORST_CASE, "logic_z002": LogicType.MANUAL, "worst_case": WorstCaseHierarchy.YES_NA_NO},
    "q3t1s5f88": {"blue_line_field": "contains_nanomaterials", "logic_z001": LogicType.WORST_CASE, "logic_z002": LogicType.MANUAL, "worst_case": WorstCaseHierarchy.YES_NA_NO},
    "q3t1s5f89": {"blue_line_field": "contains_pah", "logic_z001": LogicType.WORST_CASE, "logic_z002": LogicType.MANUAL, "worst_case": WorstCaseHierarchy.YES_NA_NO},
    "q3t1s5f92": {"blue_line_field": "contains_cmr", "logic_z001": LogicType.WORST_CASE, "logic_z002": LogicType.MANUAL, "worst_case": WorstCaseHierarchy.YES_NA_NO},
    "q3t1s5f93": {"blue_line_field": "contains_prc", "logic_z001": LogicType.WORST_CASE, "logic_z002": LogicType.MANUAL, "worst_case": WorstCaseHierarchy.YES_NA_NO},
    
    # Product characteristics (no is worst for positive claims)
    "q3t1s5f94": {"blue_line_field": "vegan", "logic_z001": LogicType.WORST_CASE, "logic_z002": LogicType.MANUAL, "worst_case": WorstCaseHierarchy.NO_NA_YES},
    "q3t1s5f95": {"blue_line_field": "contains_gluten", "logic_z001": LogicType.WORST_CASE, "logic_z002": LogicType.MANUAL, "worst_case": WorstCaseHierarchy.YES_NA_NO},
    "q3t1s5f96": {"blue_line_field": "tested_on_animals", "logic_z001": LogicType.WORST_CASE, "logic_z002": LogicType.MANUAL, "worst_case": WorstCaseHierarchy.YES_NA_NO},
    
    # Animal derived
    "q3t6s36f262": {"blue_line_field": "contains_animal_substances", "logic_z001": LogicType.WORST_CASE, "logic_z002": LogicType.MANUAL, "worst_case": WorstCaseHierarchy.YES_NA_NO},
    "q3t6s36f263": {"blue_line_field": "contains_animal_derivatives", "logic_z001": LogicType.WORST_CASE, "logic_z002": LogicType.MANUAL, "worst_case": WorstCaseHierarchy.YES_NA_NO},
    "q3t6s36f264": {"blue_line_field": "contains_bse_tse", "logic_z001": LogicType.WORST_CASE, "logic_z002": LogicType.MANUAL, "worst_case": WorstCaseHierarchy.YES_NA_NO},
    
    # Certifications
    "q3t1s3f27": {"blue_line_field": "kosher_certified", "logic_z001": LogicType.WORST_CASE, "logic_z002": LogicType.MANUAL, "worst_case": WorstCaseHierarchy.NO_NA_YES},
    "q3t1s3f28": {"blue_line_field": "halal_certified", "logic_z001": LogicType.WORST_CASE, "logic_z002": LogicType.MANUAL, "worst_case": WorstCaseHierarchy.NO_NA_YES},
    "q3t1s3f29": {"blue_line_field": "food_grade", "logic_z001": LogicType.WORST_CASE, "logic_z002": LogicType.MANUAL, "worst_case": WorstCaseHierarchy.NO_NA_YES},
    
    # Storage
    "q3t1s40f347": {"blue_line_field": "shelf_life", "logic_z001": LogicType.CONCATENATE, "logic_z002": LogicType.MANUAL},
    "q3t1s40f348": {"blue_line_field": "storage_temperature", "logic_z001": LogicType.CONCATENATE, "logic_z002": LogicType.MANUAL},
}


def apply_sap_logic(questionnaire_value: Any, sap_value: Any) -> Any:
    """
    Apply SAP logic: use SAP value, ignore questionnaire.
    
    Args:
        questionnaire_value: Value from questionnaire (ignored)
        sap_value: Value from SAP
        
    Returns:
        SAP value
    """
    return sap_value


def apply_manual_logic() -> None:
    """
    Apply MANUAL logic: leave empty for manual entry.
    
    Returns:
        None (empty value)
    """
    return None


def apply_concatenate_logic(values: List[Any]) -> str:
    """
    Apply CONCATENATE logic: combine different values with separator.
    
    Args:
        values: List of values to concatenate
        
    Returns:
        Concatenated string
    """
    # Filter out empty/None values
    non_empty = [str(v) for v in values if v not in [None, "", "NA", "N/A"]]
    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for v in non_empty:
        if v not in seen:
            seen.add(v)
            unique.append(v)
    
    return " / ".join(unique) if unique else None


def apply_worst_case_logic(values: List[Any], hierarchy: WorstCaseHierarchy) -> str:
    """
    Apply WORST_CASE logic: use worst value according to hierarchy.
    
    Args:
        values: List of values (Yes/No/NA)
        hierarchy: Which hierarchy to use
        
    Returns:
        Worst case value
    """
    # Normalize values
    normalized = []
    for v in values:
        if v is None:
            continue
        v_str = str(v).upper().strip()
        if v_str in ["YES", "Y", "1", "TRUE"]:
            normalized.append("Yes")
        elif v_str in ["NO", "N", "0", "FALSE"]:
            normalized.append("No")
        elif v_str in ["NA", "N/A", "NOT APPLICABLE"]:
            normalized.append("NA")
    
    if not normalized:
        return "NA"
    
    # Apply hierarchy
    if hierarchy == WorstCaseHierarchy.YES_NA_NO:
        # Yes is worst
        if "Yes" in normalized:
            return "Yes"
        elif "NA" in normalized:
            return "NA"
        else:
            return "No"
    else:  # NO_NA_YES
        # No is worst
        if "No" in normalized:
            return "No"
        elif "NA" in normalized:
            return "NA"
        else:
            return "Yes"


def apply_blocked_logic() -> str:
    """
    Apply BLOCKED logic: field is not editable.
    
    Returns:
        Empty string (blocked)
    """
    return ""


def get_field_rule(field_code: str) -> Optional[Dict[str, Any]]:
    """
    Get blue line rule for a field code.
    
    Args:
        field_code: Questionnaire field code
        
    Returns:
        Rule dict or None
    """
    return BLUE_LINE_FIELD_RULES.get(field_code)



