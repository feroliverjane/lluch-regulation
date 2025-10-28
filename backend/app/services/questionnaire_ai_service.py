"""
Questionnaire AI Service

Mock AI service that simulates intelligent analysis of questionnaires.
Structured to be easily replaced with real OpenAI integration later.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import random
from datetime import datetime

from app.models.questionnaire import Questionnaire
from app.models.questionnaire_validation import QuestionnaireValidation, ValidationSeverity
from app.models.questionnaire_incident import QuestionnaireIncident


class QuestionnaireAIService:
    """AI-powered analysis service (mock implementation for MVP)"""
    
    def __init__(self, db: Session, use_real_ai: bool = False):
        self.db = db
        self.use_real_ai = use_real_ai
    
    async def analyze_risk_profile(
        self,
        questionnaire_id: int
    ) -> Dict[str, Any]:
        """
        Analyze questionnaire and generate risk score with recommendations.
        
        Returns:
            {
                "risk_score": int (0-100),
                "summary": str,
                "recommendation": str,
                "confidence": float (0-1),
                "key_findings": List[str],
                "areas_of_concern": List[str]
            }
        """
        questionnaire = self.db.query(Questionnaire).filter(
            Questionnaire.id == questionnaire_id
        ).first()
        
        if not questionnaire:
            raise ValueError(f"Questionnaire {questionnaire_id} not found")
        
        # Get validations and incidents
        validations = self.db.query(QuestionnaireValidation).filter(
            QuestionnaireValidation.questionnaire_id == questionnaire_id
        ).all()
        
        incidents = self.db.query(QuestionnaireIncident).filter(
            QuestionnaireIncident.questionnaire_id == questionnaire_id
        ).all()
        
        if self.use_real_ai:
            return await self._real_ai_analysis(questionnaire, validations, incidents)
        else:
            return self._mock_ai_analysis(questionnaire, validations, incidents)
    
    def _mock_ai_analysis(
        self,
        questionnaire: Questionnaire,
        validations: List[QuestionnaireValidation],
        incidents: List[QuestionnaireIncident]
    ) -> Dict[str, Any]:
        """
        Generate realistic mock AI analysis based on validation results.
        """
        # Calculate base risk score from validations
        critical_count = sum(1 for v in validations if v.severity == ValidationSeverity.CRITICAL)
        warning_count = sum(1 for v in validations if v.severity == ValidationSeverity.WARNING)
        open_incidents = sum(1 for i in incidents if i.status.value == "OPEN")
        
        # Risk score calculation
        risk_score = 0
        risk_score += critical_count * 20  # Each critical adds 20 points
        risk_score += warning_count * 10   # Each warning adds 10 points
        risk_score += open_incidents * 15  # Each open incident adds 15 points
        risk_score = min(risk_score, 100)  # Cap at 100
        
        # Determine recommendation based on risk score
        if risk_score >= 70:
            recommendation = "REJECT"
            confidence = 0.85
        elif risk_score >= 40:
            recommendation = "REVIEW"
            confidence = 0.75
        else:
            recommendation = "APPROVE"
            confidence = 0.90
        
        # Generate summary
        summary_parts = []
        
        if critical_count > 0:
            summary_parts.append(
                f"⚠️ Identified {critical_count} critical deviation{'s' if critical_count > 1 else ''} "
                f"from expected Blue Line values that require immediate attention."
            )
        
        if warning_count > 0:
            summary_parts.append(
                f"Found {warning_count} moderate deviation{'s' if warning_count > 1 else ''} "
                f"that should be reviewed but may be acceptable."
            )
        
        if questionnaire.questionnaire_type.value == "REHOMOLOGATION":
            summary_parts.append(
                f"This is a rehomologation (version {questionnaire.version}). "
                f"Changes have been detected compared to the previous version."
            )
        
        if risk_score < 30:
            summary_parts.append(
                "✅ Overall, the questionnaire responses align well with expected parameters. "
                "The material-supplier pair appears to maintain consistent quality standards."
            )
        elif risk_score < 70:
            summary_parts.append(
                "⚠️ Some concerns have been identified that warrant further review before approval. "
                "Manual verification is recommended for flagged items."
            )
        else:
            summary_parts.append(
                "🚨 Significant deviations detected. This submission requires thorough investigation "
                "and supplier engagement before proceeding with homologation."
            )
        
        summary = " ".join(summary_parts)
        
        # Generate key findings
        key_findings = []
        for v in validations[:5]:  # Top 5 findings
            if v.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.WARNING]:
                key_findings.append(
                    f"{v.field_name}: {v.message}"
                )
        
        if not key_findings:
            key_findings = [
                "All responses are within acceptable parameters",
                "No significant deviations from baseline detected",
                "Questionnaire completeness: 100%"
            ]
        
        # Generate areas of concern
        areas_of_concern = []
        for v in validations:
            if v.severity == ValidationSeverity.CRITICAL:
                areas_of_concern.append(v.field_name)
        
        if not areas_of_concern:
            areas_of_concern = ["None identified"]
        
        return {
            "risk_score": risk_score,
            "summary": summary,
            "recommendation": recommendation,
            "confidence": confidence,
            "key_findings": key_findings[:5],
            "areas_of_concern": list(set(areas_of_concern))[:5]
        }
    
    async def _real_ai_analysis(
        self,
        questionnaire: Questionnaire,
        validations: List[QuestionnaireValidation],
        incidents: List[QuestionnaireIncident]
    ) -> Dict[str, Any]:
        """
        Real AI analysis using OpenAI API (to be implemented).
        
        This method would:
        1. Construct a detailed prompt with questionnaire data
        2. Call OpenAI API
        3. Parse structured response
        4. Return analysis results
        """
        # TODO: Implement OpenAI integration
        # For now, fall back to mock
        return self._mock_ai_analysis(questionnaire, validations, incidents)
    
    def generate_change_summary(
        self,
        current_questionnaire_id: int,
        previous_questionnaire_id: int
    ) -> str:
        """Generate natural language summary of changes between versions"""
        current = self.db.query(Questionnaire).filter(
            Questionnaire.id == current_questionnaire_id
        ).first()
        
        previous = self.db.query(Questionnaire).filter(
            Questionnaire.id == previous_questionnaire_id
        ).first()
        
        if not current or not previous:
            return "Unable to compare: questionnaire not found"
        
        current_responses = current.responses or {}
        previous_responses = previous.responses or {}
        
        changes = []
        added = []
        removed = []
        
        all_fields = set(current_responses.keys()) | set(previous_responses.keys())
        
        for field in all_fields:
            if field in current_responses and field in previous_responses:
                if current_responses[field] != previous_responses[field]:
                    changes.append(field)
            elif field in current_responses:
                added.append(field)
            else:
                removed.append(field)
        
        # Generate summary
        summary_parts = []
        
        if changes:
            summary_parts.append(
                f"📝 {len(changes)} field{'s' if len(changes) > 1 else ''} modified: {', '.join(changes[:3])}"
                + (f" and {len(changes) - 3} more" if len(changes) > 3 else "")
            )
        
        if added:
            summary_parts.append(
                f"➕ {len(added)} new field{'s' if len(added) > 1 else ''} added"
            )
        
        if removed:
            summary_parts.append(
                f"➖ {len(removed)} field{'s' if len(removed) > 1 else ''} removed"
            )
        
        if not summary_parts:
            return "✅ No changes detected between versions"
        
        return " | ".join(summary_parts)
    
    def evaluate_sustainability_score(self, questionnaire: Questionnaire) -> Dict[str, Any]:
        """
        Evaluate sustainability aspects of the questionnaire.
        
        Mock implementation - checks for sustainability-related fields.
        """
        responses = questionnaire.responses or {}
        
        score = 50  # Base score
        factors = []
        
        # Check for sustainability indicators
        if responses.get("organic_certified") == "Yes":
            score += 20
            factors.append("Organic certification: +20")
        
        if responses.get("fair_trade_certified") == "Yes":
            score += 15
            factors.append("Fair trade certification: +15")
        
        if responses.get("sustainable_sourcing") == "Yes":
            score += 15
            factors.append("Sustainable sourcing: +15")
        
        if responses.get("carbon_neutral") == "Yes":
            score += 10
            factors.append("Carbon neutral: +10")
        
        # Negative factors
        if responses.get("endangered_species_used") == "Yes":
            score -= 30
            factors.append("Endangered species used: -30")
        
        score = max(0, min(score, 100))  # Clamp between 0-100
        
        return {
            "score": score,
            "factors": factors,
            "rating": "Excellent" if score >= 80 else "Good" if score >= 60 else "Fair" if score >= 40 else "Poor"
        }

