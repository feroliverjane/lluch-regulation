"""
Questionnaire Validation Service

Handles validation of questionnaire responses against:
1. Blue Line expected values
2. Previous questionnaire versions
3. Configurable thresholds
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.questionnaire import Questionnaire, QuestionnaireStatus
from app.models.questionnaire_validation import QuestionnaireValidation, ValidationType, ValidationSeverity
from app.models.questionnaire_incident import QuestionnaireIncident, IncidentStatus, ResolutionAction
from app.models.blue_line import BlueLine
from app.models.material import Material
from app.services.questionnaire_field_mapper import QuestionnaireFieldMapper


class QuestionnaireValidationService:
    """Service for validating questionnaires"""
    
    # Configuration thresholds (can be moved to settings)
    WARNING_THRESHOLD = 5.0  # 5% deviation
    CRITICAL_THRESHOLD = 10.0  # 10% deviation
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_questionnaire(self, questionnaire_id: int) -> List[QuestionnaireValidation]:
        """
        Main validation entry point.
        Runs all validations and creates incidents for critical issues.
        """
        questionnaire = self.db.query(Questionnaire).filter(
            Questionnaire.id == questionnaire_id
        ).first()
        
        if not questionnaire:
            raise ValueError(f"Questionnaire {questionnaire_id} not found")
        
        validations = []
        
        # 1. Compare with Blue Line
        blue_line_validations = self.compare_with_blue_line(questionnaire)
        validations.extend(blue_line_validations)
        
        # 2. Compare with previous version (if rehomologation)
        if questionnaire.previous_version_id:
            version_validations = self.compare_with_previous_version(questionnaire)
            validations.extend(version_validations)
        
        # 3. Save all validations
        for validation in validations:
            self.db.add(validation)
        self.db.commit()
        
        # 4. Auto-create incidents for critical validations
        self._auto_create_incidents(questionnaire, validations)
        
        return validations
    
    def compare_with_blue_line(self, questionnaire: Questionnaire) -> List[QuestionnaireValidation]:
        """Compare questionnaire responses with Blue Line expected values
        
        The Blue Line is associated with a material (not a supplier).
        When a questionnaire arrives from a supplier, it is compared against 
        the Blue Line for that material.
        """
        validations = []
        
        # Get Blue Line for this material (one Blue Line per material)
        blue_line = self.db.query(BlueLine).filter(
            BlueLine.material_id == questionnaire.material_id
        ).first()
        
        if not blue_line:
            # No Blue Line exists - INFO level notification
            validation = QuestionnaireValidation(
                questionnaire_id=questionnaire.id,
                validation_type=ValidationType.BLUE_LINE_COMPARISON,
                field_name="general",
                severity=ValidationSeverity.INFO,
                requires_action=False,
                message=f"No Blue Line exists for material {questionnaire.material_id}. This questionnaire will be compared against future Blue Line when created."
            )
            validations.append(validation)
            return validations
        
        # Compare key fields using responses format (Lluch format)
        # Blue Line responses are organized by fieldCode (e.g., "q3t1s2f15": {"value": "...", "name": "...", "type": "..."})
        blue_line_responses = blue_line.responses or {}
        questionnaire_responses = questionnaire.responses or {}
        
        # Get all critical fieldCodes to validate
        critical_field_codes = QuestionnaireFieldMapper.get_all_critical_fields()
        
        for field_code in critical_field_codes:
            # Check if this field exists in questionnaire responses
            if field_code not in questionnaire_responses:
                continue
            
            # Get field name
            field_name = QuestionnaireFieldMapper.get_field_name(field_code)
            
            # Get values from responses format
            questionnaire_field_data = questionnaire_responses[field_code]
            actual_value = QuestionnaireFieldMapper.extract_simple_value(questionnaire_field_data)
            actual_normalized = QuestionnaireFieldMapper.normalize_value(field_code, actual_value)
            
            # Check if Blue Line has expected value for this fieldCode
            if field_code in blue_line_responses:
                blue_line_field_data = blue_line_responses[field_code]
                expected_value = QuestionnaireFieldMapper.extract_simple_value(blue_line_field_data)
                expected_normalized = QuestionnaireFieldMapper.normalize_value(field_code, expected_value)
                
                if expected_normalized != actual_normalized:
                    # Calculate deviation for numeric fields
                    deviation_pct = self._calculate_deviation(expected_normalized, actual_normalized)
                    severity = self._determine_severity(deviation_pct)
                    
                    # Override severity for critical fields
                    if QuestionnaireFieldMapper.is_critical_field(field_code) and severity == ValidationSeverity.WARNING:
                        severity = ValidationSeverity.CRITICAL
                    
                    validation = QuestionnaireValidation(
                        questionnaire_id=questionnaire.id,
                        validation_type=ValidationType.BLUE_LINE_COMPARISON,
                        field_name=f"{field_code}:{field_name}",
                        expected_value=expected_normalized,
                        actual_value=actual_normalized,
                        deviation_percentage=deviation_pct,
                        severity=severity,
                        requires_action=(severity == ValidationSeverity.CRITICAL),
                        message=f"{field_name}: expected '{expected_normalized}', got '{actual_normalized}'"
                    )
                    validations.append(validation)
        
        # Legacy support: also check blue_line_data format for backward compatibility
        blue_line_data = blue_line.blue_line_data or {}
        if blue_line_data and not blue_line_responses:
            # Only use legacy format if responses is empty
            for field_code in critical_field_codes:
                if field_code not in questionnaire_responses:
                    continue
                
                bl_field = QuestionnaireFieldMapper.get_blue_line_field(field_code)
                field_name = QuestionnaireFieldMapper.get_field_name(field_code)
                
                if bl_field and bl_field in blue_line_data:
                    questionnaire_field_data = questionnaire_responses[field_code]
                    actual_value = QuestionnaireFieldMapper.extract_simple_value(questionnaire_field_data)
                    actual_normalized = QuestionnaireFieldMapper.normalize_value(field_code, actual_value)
                    expected = str(blue_line_data[bl_field])
                    
                    if expected != actual_normalized:
                        deviation_pct = self._calculate_deviation(expected, actual_normalized)
                        severity = self._determine_severity(deviation_pct)
                        
                        if QuestionnaireFieldMapper.is_critical_field(field_code) and severity == ValidationSeverity.WARNING:
                            severity = ValidationSeverity.CRITICAL
                        
                        validation = QuestionnaireValidation(
                            questionnaire_id=questionnaire.id,
                            validation_type=ValidationType.BLUE_LINE_COMPARISON,
                            field_name=f"{field_code}:{field_name}",
                            expected_value=expected,
                            actual_value=actual_normalized,
                            deviation_percentage=deviation_pct,
                            severity=severity,
                            requires_action=(severity == ValidationSeverity.CRITICAL),
                            message=f"{field_name}: expected '{expected}', got '{actual_normalized}'"
                        )
                        validations.append(validation)
        
        return validations
    
    def compare_with_previous_version(self, questionnaire: Questionnaire) -> List[QuestionnaireValidation]:
        """Compare with previous questionnaire version"""
        validations = []
        
        if not questionnaire.previous_version_id:
            return validations
        
        previous = self.db.query(Questionnaire).filter(
            Questionnaire.id == questionnaire.previous_version_id
        ).first()
        
        if not previous:
            return validations
        
        current_responses = questionnaire.responses or {}
        previous_responses = previous.responses or {}
        
        # Find changed fields
        all_fields = set(current_responses.keys()) | set(previous_responses.keys())
        
        for field_name in all_fields:
            current_value = str(current_responses.get(field_name, ""))
            previous_value = str(previous_responses.get(field_name, ""))
            
            if current_value != previous_value:
                deviation_pct = self._calculate_deviation(previous_value, current_value)
                
                # For version comparison, only flag significant changes
                if deviation_pct and deviation_pct > self.WARNING_THRESHOLD:
                    validation = QuestionnaireValidation(
                        questionnaire_id=questionnaire.id,
                        validation_type=ValidationType.VERSION_COMPARISON,
                        field_name=field_name,
                        expected_value=previous_value,
                        actual_value=current_value,
                        deviation_percentage=deviation_pct,
                        severity=ValidationSeverity.INFO,
                        requires_action=False,
                        message=f"Changed from v{previous.version}: '{previous_value}' -> '{current_value}'"
                    )
                    validations.append(validation)
        
        return validations
    
    def _calculate_deviation(self, expected: str, actual: str) -> Optional[float]:
        """Calculate percentage deviation for numeric values"""
        try:
            expected_num = float(expected)
            actual_num = float(actual)
            
            if expected_num == 0:
                return 100.0 if actual_num != 0 else 0.0
            
            deviation = abs((actual_num - expected_num) / expected_num) * 100
            return round(deviation, 2)
        except (ValueError, TypeError):
            # Not numeric, can't calculate deviation
            return None
    
    def _determine_severity(self, deviation_pct: Optional[float]) -> ValidationSeverity:
        """Determine severity based on deviation percentage"""
        if deviation_pct is None:
            return ValidationSeverity.WARNING
        
        if deviation_pct >= self.CRITICAL_THRESHOLD:
            return ValidationSeverity.CRITICAL
        elif deviation_pct >= self.WARNING_THRESHOLD:
            return ValidationSeverity.WARNING
        else:
            return ValidationSeverity.INFO
    
    def _auto_create_incidents(
        self,
        questionnaire: Questionnaire,
        validations: List[QuestionnaireValidation]
    ) -> None:
        """Automatically create incidents for critical validations"""
        for validation in validations:
            if validation.severity == ValidationSeverity.CRITICAL and validation.requires_action:
                # Check if incident already exists for this validation
                existing = self.db.query(QuestionnaireIncident).filter(
                    QuestionnaireIncident.questionnaire_id == questionnaire.id,
                    QuestionnaireIncident.field_name == validation.field_name,
                    QuestionnaireIncident.status.in_([IncidentStatus.OPEN, IncidentStatus.ESCALATED_TO_SUPPLIER])
                ).first()
                
                if not existing:
                    incident = QuestionnaireIncident(
                        questionnaire_id=questionnaire.id,
                        validation_id=validation.id,
                        field_name=validation.field_name,
                        issue_description=validation.message or f"Critical deviation detected in {validation.field_name}",
                        status=IncidentStatus.OPEN,
                        resolution_action=ResolutionAction.PENDING
                    )
                    self.db.add(incident)
        
        self.db.commit()
    
    def get_validation_summary(self, questionnaire_id: int) -> Dict[str, Any]:
        """Get a summary of all validations for a questionnaire"""
        validations = self.db.query(QuestionnaireValidation).filter(
            QuestionnaireValidation.questionnaire_id == questionnaire_id
        ).all()
        
        summary = {
            "total": len(validations),
            "by_severity": {
                "CRITICAL": 0,
                "WARNING": 0,
                "INFO": 0
            },
            "requires_action": 0,
            "validations": []
        }
        
        for v in validations:
            summary["by_severity"][v.severity.value] += 1
            if v.requires_action:
                summary["requires_action"] += 1
            summary["validations"].append({
                "id": v.id,
                "field_name": v.field_name,
                "severity": v.severity.value,
                "message": v.message
            })
        
        return summary

