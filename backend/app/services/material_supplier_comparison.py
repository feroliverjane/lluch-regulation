"""
Material-Supplier Comparison Service

Compares questionnaire responses against Blue Line for the 10 most relevant material-specific fields.
Excludes supplier-specific fields like Supplier Name.
"""

from typing import Dict, Any, List, Optional
from app.models.questionnaire import Questionnaire
from app.models.blue_line import BlueLine
from app.services.questionnaire_field_mapper import QuestionnaireFieldMapper
from app.schemas.material_supplier import MismatchField, ComparisonResult


class MaterialSupplierComparisonService:
    """Service for comparing questionnaires with Blue Lines"""
    
    # The 10 material-specific fields to compare (excluding Supplier Name)
    MATERIAL_COMPARISON_FIELDS = [
        "q3t1s2f16",  # Product Name
        "q3t1s2f17",  # Product Code
        "q3t1s2f23",  # CAS Number
        "q3t1s3f27",  # Kosher Certificate
        "q3t1s3f28",  # Halal Certificate
        "q3t1s3f29",  # Food/Flavour Grade
        "q3t1s4f33",  # Country of Botanical Origin
        "q3t1s4f38",  # Botanical Name
        "q3t1s4f44",  # 100% Natural
        "q3t1s4f46",  # 100% Pure
    ]
    
    @classmethod
    def compare_questionnaire_with_blue_line(
        cls,
        questionnaire: Questionnaire,
        blue_line: BlueLine
    ) -> ComparisonResult:
        """
        Compare questionnaire responses with Blue Line for the 10 material-specific fields.
        
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
        
        matches = 0
        mismatches: List[MismatchField] = []
        
        # Compare each of the 10 material-specific fields
        for field_code in cls.MATERIAL_COMPARISON_FIELDS:
            # Get field name
            field_name = QuestionnaireFieldMapper.get_field_name(field_code)
            
            # Get values from questionnaire
            questionnaire_field_data = questionnaire_responses.get(field_code)
            if not questionnaire_field_data:
                # Field missing in questionnaire - consider as mismatch
                blue_line_value = cls._get_blue_line_value(blue_line_responses, field_code)
                mismatches.append(MismatchField(
                    field_code=field_code,
                    field_name=field_name,
                    expected_value=blue_line_value,
                    actual_value=None,
                    severity="WARNING",
                    accepted=False
                ))
                continue
            
            # Extract and normalize values
            questionnaire_value = QuestionnaireFieldMapper.extract_simple_value(questionnaire_field_data)
            questionnaire_normalized = QuestionnaireFieldMapper.normalize_value(field_code, questionnaire_value)
            
            blue_line_value = cls._get_blue_line_value(blue_line_responses, field_code)
            if blue_line_value is None:
                # Field missing in Blue Line - skip comparison
                continue
            
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
        
        # Calculate validation score (0-100)
        total_fields = len(cls.MATERIAL_COMPARISON_FIELDS)
        score = int((matches / total_fields) * 100) if total_fields > 0 else 0
        
        return ComparisonResult(
            blue_line_exists=True,
            matches=matches,
            mismatches=mismatches,
            score=score,
            message=f"Compared {matches} matches out of {total_fields} material-specific fields"
        )
    
    @classmethod
    def _get_blue_line_value(cls, blue_line_responses: Dict[str, Any], field_code: str) -> Optional[str]:
        """Extract value from Blue Line responses for a given fieldCode"""
        field_data = blue_line_responses.get(field_code)
        if not field_data:
            return None
        
        value = QuestionnaireFieldMapper.extract_simple_value(field_data)
        return value
    
    @classmethod
    def calculate_validation_score(
        cls,
        matches: int,
        total_fields: int = None
    ) -> int:
        """
        Calculate validation score (0-100) based on matches.
        
        Args:
            matches: Number of matching fields
            total_fields: Total number of fields (defaults to 10)
            
        Returns:
            Score from 0 to 100
        """
        if total_fields is None:
            total_fields = len(cls.MATERIAL_COMPARISON_FIELDS)
        
        if total_fields == 0:
            return 0
        
        return int((matches / total_fields) * 100)

