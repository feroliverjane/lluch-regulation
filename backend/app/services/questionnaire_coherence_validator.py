"""
Questionnaire Coherence Validator

AI-based validation service that checks logical consistency of questionnaire responses.
Uses rule-based logic to detect contradictions and inconsistencies.
"""

import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.models.questionnaire import Questionnaire

logger = logging.getLogger(__name__)


class CoherenceIssue:
    """Represents a coherence validation issue"""
    
    def __init__(self, field: str, issue: str, severity: str):
        self.field = field
        self.issue = issue
        self.severity = severity  # "info", "warning", "critical"
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "field": self.field,
            "issue": self.issue,
            "severity": self.severity
        }


class QuestionnaireCoherenceValidator:
    """
    Validates logical coherence of questionnaire responses.
    Checks for contradictions between related fields.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.issues: List[CoherenceIssue] = []
    
    def validate_coherence(self, questionnaire_id: int) -> Tuple[int, List[Dict[str, str]]]:
        """
        Validate questionnaire coherence and return score + issues.
        
        Args:
            questionnaire_id: ID of questionnaire to validate
            
        Returns:
            Tuple of (score 0-100, list of issue dicts)
        """
        questionnaire = self.db.query(Questionnaire).filter(
            Questionnaire.id == questionnaire_id
        ).first()
        
        if not questionnaire:
            raise ValueError(f"Questionnaire {questionnaire_id} not found")
        
        if not questionnaire.responses:
            logger.warning(f"Questionnaire {questionnaire_id} has no responses")
            return 0, []
        
        self.issues = []
        responses = questionnaire.responses
        
        # Run all validation checks
        self._check_natural_vs_additives(responses)
        self._check_vegan_vs_animal_origin(responses)
        self._check_certifications(responses)
        self._check_organic_vs_pesticides(responses)
        self._check_gmo_consistency(responses)
        self._check_allergens(responses)
        self._check_rspo_consistency(responses)
        self._check_fermentation_gmo(responses)
        self._check_halal_consistency(responses)
        self._check_kosher_consistency(responses)
        
        # Calculate score: 100 - (points deducted per issue)
        score = self._calculate_score()
        
        # Convert issues to dict format
        issues_dict = [issue.to_dict() for issue in self.issues]
        
        logger.info(
            f"Questionnaire {questionnaire_id} coherence validation: "
            f"score={score}, issues={len(issues_dict)}"
        )
        
        # Update questionnaire with results
        questionnaire.ai_coherence_score = score
        questionnaire.ai_coherence_details = issues_dict
        self.db.commit()
        
        return score, issues_dict
    
    def _calculate_score(self) -> int:
        """Calculate coherence score based on issues found"""
        if not self.issues:
            return 100
        
        # Deduct points based on severity
        deductions = {
            "critical": 20,
            "warning": 10,
            "info": 3
        }
        
        total_deduction = sum(
            deductions.get(issue.severity, 5) for issue in self.issues
        )
        
        score = max(0, 100 - total_deduction)
        return score
    
    def _get_field_value(self, responses: Dict[str, Any], field_code: str) -> Any:
        """Extract value from field response (handles both string and dict formats)"""
        field_data = responses.get(field_code)
        if not field_data:
            return None
        
        if isinstance(field_data, dict):
            return field_data.get("value")
        return field_data
    
    def _check_natural_vs_additives(self, responses: Dict[str, Any]):
        """Check if 100% natural but contains synthetic additives"""
        is_natural = self._get_field_value(responses, "q3t1s4f44")  # 100% Natural
        has_additives = self._get_field_value(responses, "q3t1s5f47")  # Contains additives
        
        if is_natural in ["Yes", "YES", "Y", "1", True] and has_additives in ["Yes", "YES", "Y", "1", True]:
            self.issues.append(CoherenceIssue(
                field="q3t1s4f44",
                issue="Product claims to be 100% natural but indicates it contains additives",
                severity="critical"
            ))
    
    def _check_vegan_vs_animal_origin(self, responses: Dict[str, Any]):
        """Check if vegan but contains animal-derived substances"""
        is_vegan = self._get_field_value(responses, "q3t1s5f94")  # Vegan
        has_animal = self._get_field_value(responses, "q3t6s36f262")  # Contains animal origin substances
        has_derivatives = self._get_field_value(responses, "q3t6s36f263")  # Contains animal derivatives
        
        if is_vegan in ["Yes", "YES", "Y", "1", True]:
            if has_animal in ["Yes", "YES", "Y", "1", True]:
                self.issues.append(CoherenceIssue(
                    field="q3t1s5f94",
                    issue="Product claims to be vegan but contains animal origin substances",
                    severity="critical"
                ))
            if has_derivatives in ["Yes", "YES", "Y", "1", True]:
                self.issues.append(CoherenceIssue(
                    field="q3t1s5f94",
                    issue="Product claims to be vegan but contains animal derivatives",
                    severity="critical"
                ))
    
    def _check_certifications(self, responses: Dict[str, Any]):
        """Check if claims certification but doesn't have certificate"""
        # Kosher
        kosher_certified = self._get_field_value(responses, "q3t1s3f27")  # Kosher Certificate
        if kosher_certified in ["Yes", "YES", "Y", "1", True]:
            # Could check for certificate attachment here
            pass
        
        # Halal
        halal_certified = self._get_field_value(responses, "q3t1s3f28")  # Halal Certificate
        if halal_certified in ["Yes", "YES", "Y", "1", True]:
            # Could check for certificate attachment here
            pass
    
    def _check_organic_vs_pesticides(self, responses: Dict[str, Any]):
        """Check if organic but uses pesticides"""
        is_organic = self._get_field_value(responses, "q3t1s4f42")  # Organic certified
        uses_pesticides = self._get_field_value(responses, "q3t1s5f108")  # Use of pesticides
        
        if is_organic in ["Yes", "YES", "Y", "1", True] and uses_pesticides in ["Yes", "YES", "Y", "1", True]:
            self.issues.append(CoherenceIssue(
                field="q3t1s4f42",
                issue="Product claims to be organic but indicates use of pesticides",
                severity="critical"
            ))
    
    def _check_gmo_consistency(self, responses: Dict[str, Any]):
        """Check GMO related consistency"""
        produced_with_gmo = self._get_field_value(responses, "q3t1s5f86")  # Produced with GMO
        requires_gmo_label = self._get_field_value(responses, "q3t1s5f87")  # Requires GMO label
        
        # If produced with GMO, should probably require labeling
        if produced_with_gmo in ["Yes", "YES", "Y", "1", True]:
            if requires_gmo_label in ["No", "NO", "N", "0", False]:
                self.issues.append(CoherenceIssue(
                    field="q3t1s5f87",
                    issue="Product is produced with GMO but doesn't require GMO labeling (verify regulation)",
                    severity="warning"
                ))
    
    def _check_allergens(self, responses: Dict[str, Any]):
        """Check allergen consistency"""
        # Contains gluten
        contains_gluten = self._get_field_value(responses, "q3t1s5f95")  # Contains gluten
        
        # If vegan and contains gluten, warn about cross-contamination
        is_vegan = self._get_field_value(responses, "q3t1s5f94")
        if is_vegan in ["Yes", "YES", "Y", "1", True] and contains_gluten in ["Yes", "YES", "Y", "1", True]:
            # This is not necessarily contradictory (gluten is plant-based), just FYI
            self.issues.append(CoherenceIssue(
                field="q3t1s5f95",
                issue="Product is vegan and contains gluten (verify if intentional)",
                severity="info"
            ))
    
    def _check_rspo_consistency(self, responses: Dict[str, Any]):
        """Check RSPO certification consistency"""
        is_member = self._get_field_value(responses, "q3t1s4f54")  # RSPO member
        product_certified = self._get_field_value(responses, "q3t1s4f55")  # Product RSPO certified
        manufacturer_rspo = self._get_field_value(responses, "q3t1s4f56")  # Manufacturer RSPO
        
        # If product is certified RSPO, member/manufacturer should be too
        if product_certified in ["Yes", "YES", "Y", "1", True]:
            if is_member in ["No", "NO", "N", "0", False]:
                self.issues.append(CoherenceIssue(
                    field="q3t1s4f54",
                    issue="Product is RSPO certified but supplier is not RSPO member",
                    severity="warning"
                ))
    
    def _check_fermentation_gmo(self, responses: Dict[str, Any]):
        """Check fermentation GMO consistency"""
        biocatalyst_gmo = self._get_field_value(responses, "q3t1s4f59")  # Biocatalyst is GMO
        produced_with_gmo = self._get_field_value(responses, "q3t1s5f86")  # Produced with GMO
        
        # If biocatalyst is GMO, product is produced with GMO
        if biocatalyst_gmo in ["Yes", "YES", "Y", "1", True]:
            if produced_with_gmo in ["No", "NO", "N", "0", False]:
                self.issues.append(CoherenceIssue(
                    field="q3t1s5f86",
                    issue="Biocatalyst used is GMO but product not marked as produced with GMO",
                    severity="critical"
                ))
    
    def _check_halal_consistency(self, responses: Dict[str, Any]):
        """Check Halal certification consistency"""
        halal_certified = self._get_field_value(responses, "q3t1s3f28")  # Halal certificate
        contains_animal = self._get_field_value(responses, "q3t6s36f262")  # Contains animal ingredients
        uses_ethanol = self._get_field_value(responses, "q3t6s36f268")  # Product contains ethanol
        
        if halal_certified in ["Yes", "YES", "Y", "1", True]:
            # Check ethanol usage
            if uses_ethanol in ["Yes", "YES", "Y", "1", True]:
                self.issues.append(CoherenceIssue(
                    field="q3t1s3f28",
                    issue="Product claims Halal certification but contains ethanol",
                    severity="critical"
                ))
            
            # If contains animal, should specify halal source
            if contains_animal in ["Yes", "YES", "Y", "1", True]:
                self.issues.append(CoherenceIssue(
                    field="q3t6s36f262",
                    issue="Halal product contains animal ingredients (verify halal source)",
                    severity="warning"
                ))
    
    def _check_kosher_consistency(self, responses: Dict[str, Any]):
        """Check Kosher certification consistency"""
        kosher_certified = self._get_field_value(responses, "q3t1s3f27")  # Kosher certificate
        contains_animal = self._get_field_value(responses, "q3t6s36f262")  # Contains animal ingredients
        
        if kosher_certified in ["Yes", "YES", "Y", "1", True] and contains_animal in ["Yes", "YES", "Y", "1", True]:
            # If contains animal, should specify kosher source
            self.issues.append(CoherenceIssue(
                field="q3t6s36f262",
                issue="Kosher product contains animal ingredients (verify kosher source)",
                severity="warning"
            ))












