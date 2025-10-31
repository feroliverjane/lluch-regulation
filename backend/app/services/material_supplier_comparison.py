"""
Material-Supplier Comparison Service

Compares questionnaire responses against Blue Line for ALL fields present in both.
Excludes supplier-specific fields like Supplier Name.
Prioritizes critical fields in results ordering.
"""

from typing import Dict, Any, List, Optional, Set
from app.models.questionnaire import Questionnaire
from app.models.blue_line import BlueLine
from app.services.questionnaire_field_mapper import QuestionnaireFieldMapper
from app.schemas.material_supplier import MismatchField, ComparisonResult


class MaterialSupplierComparisonService:
    """Service for comparing questionnaires with Blue Lines"""
    
    # Supplier-specific fields to exclude from comparison
    EXCLUDED_FIELDS = {
        "q3t1s2f15",  # Supplier Name - supplier-specific, not material-specific
    }
    
    @classmethod
    def compare_questionnaire_with_blue_line(
        cls,
        questionnaire: Questionnaire,
        blue_line: BlueLine
    ) -> ComparisonResult:
        """
        Compare questionnaire responses with Blue Line for ALL common fields.
        
        Compares every field that exists in both the questionnaire and Blue Line,
        excluding supplier-specific fields. Critical fields are prioritized in results.
        
        Args:
            questionnaire: Questionnaire to compare
            blue_line: Blue Line to compare against
            
        Returns:
            ComparisonResult with matches, mismatches, and score
        """
        if not blue_line:
            return ComparisonResult(
                blue_line_exists=False,
                matches=0,
                mismatches=[],
                score=0,
                message="No Blue Line exists for this material"
            )
        
        questionnaire_responses = questionnaire.responses or {}
        blue_line_responses = blue_line.responses or {}
        
        # Get all fieldCodes from both sources (excluding metadata fields)
        questionnaire_fields = cls._get_valid_field_codes(questionnaire_responses)
        blue_line_fields = cls._get_valid_field_codes(blue_line_responses)
        
        # Fields to compare: intersection of both (fields present in both)
        fields_to_compare = questionnaire_fields.intersection(blue_line_fields)
        
        # Exclude supplier-specific fields
        fields_to_compare = fields_to_compare - cls.EXCLUDED_FIELDS
        
        if not fields_to_compare:
            return ComparisonResult(
                blue_line_exists=True,
                matches=0,
                mismatches=[],
                score=0,
                message="No common fields found to compare between questionnaire and Blue Line"
            )
        
        matches = 0
        mismatches: List[MismatchField] = []
        
        # Sort fields: critical fields first, then by field_code
        sorted_fields = sorted(
            fields_to_compare,
            key=lambda fc: (
                not QuestionnaireFieldMapper.is_critical_field(fc),  # Critical first (False sorts before True)
                fc  # Then alphabetically
            )
        )
        
        # Compare each field
        for field_code in sorted_fields:
            # Get field name
            field_name = QuestionnaireFieldMapper.get_field_name(field_code)
            
            # Get values from questionnaire
            questionnaire_field_data = questionnaire_responses.get(field_code)
            blue_line_field_data = blue_line_responses.get(field_code)
            
            if not questionnaire_field_data or not blue_line_field_data:
                # Skip if either is missing
                continue
            
            # Extract and normalize values
            questionnaire_value = QuestionnaireFieldMapper.extract_simple_value(questionnaire_field_data)
            questionnaire_normalized = QuestionnaireFieldMapper.normalize_value(field_code, questionnaire_value)
            
            blue_line_value = QuestionnaireFieldMapper.extract_simple_value(blue_line_field_data)
            blue_line_normalized = QuestionnaireFieldMapper.normalize_value(field_code, blue_line_value)
            
            # Compare values
            if questionnaire_normalized == blue_line_normalized:
                matches += 1
            else:
                # Determine severity based on field criticality
                severity = "CRITICAL" if QuestionnaireFieldMapper.is_critical_field(field_code) else "WARNING"
                
                mismatches.append(MismatchField(
                    field_code=field_code,
                    field_name=field_name,
                    expected_value=blue_line_normalized,
                    actual_value=questionnaire_normalized,
                    severity=severity,
                    accepted=False
                ))
        
        # Calculate validation score (0-100) based on all compared fields
        total_fields = len(sorted_fields)
        score = int((matches / total_fields) * 100) if total_fields > 0 else 0
        
        return ComparisonResult(
            blue_line_exists=True,
            matches=matches,
            mismatches=mismatches,
            score=score,
            message=f"Compared {matches} matches out of {total_fields} common fields"
        )
    
    @classmethod
    def _get_valid_field_codes(cls, responses: Dict[str, Any]) -> Set[str]:
        """
        Extract valid fieldCodes from responses, excluding metadata fields.
        
        Args:
            responses: Dictionary of responses (fieldCode -> field_data)
            
        Returns:
            Set of valid fieldCodes
        """
        valid_fields = set()
        
        for field_code, field_data in responses.items():
            # Skip metadata fields (starting with underscore)
            if field_code.startswith("_"):
                continue
            
            # Skip empty or None values
            if not field_data:
                continue
            
            # Only include fields that have actual data
            # Field data can be a dict with "value" or a simple value
            if isinstance(field_data, dict):
                value = field_data.get("value", "")
                if value or value == 0 or value is False:  # Include False, 0, empty string
                    valid_fields.add(field_code)
            elif field_data:  # Simple value (string, number, boolean)
                valid_fields.add(field_code)
        
        return valid_fields
    
    @classmethod
    def calculate_validation_score(
        cls,
        matches: int,
        total_fields: int
    ) -> int:
        """
        Calculate validation score (0-100) based on matches.
        
        Args:
            matches: Number of matching fields
            total_fields: Total number of fields compared
            
        Returns:
            Score from 0 to 100
        """
        if total_fields == 0:
            return 0
        
        return int((matches / total_fields) * 100)

