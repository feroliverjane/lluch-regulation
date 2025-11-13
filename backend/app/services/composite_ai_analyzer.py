"""
AI-powered Composite Comparison Analyzer

Uses OpenAI to analyze differences between Z1 and Z2 composites and provide
contextual insights about the changes.
"""

import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from app.core.config import settings
from app.models.composite import Composite, CompositeComponent

logger = logging.getLogger(__name__)


class CompositeAIAnalyzer:
    """
    Analyzes composite differences using AI to provide contextual insights.
    """
    
    def __init__(self, db: Session, api_key: Optional[str] = None):
        """
        Initialize AI analyzer.
        
        Args:
            db: Database session
            api_key: OpenAI API key (optional, will use from settings if not provided)
        """
        self.db = db
        
        if OPENAI_AVAILABLE:
            self.client = OpenAI(api_key=api_key or settings.OPENAI_API_KEY) if (api_key or settings.OPENAI_API_KEY) else None
            self.model = "gpt-4o"
        else:
            self.client = None
            logger.warning("OpenAI not available. AI analysis will be disabled.")
    
    def analyze_z1_to_z2_changes(
        self,
        z1_composite: Composite,
        z2_composite: Composite,
        comparison_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze changes from Z1 to Z2 composite using AI.
        
        Args:
            z1_composite: The original Z1 composite
            z2_composite: The new Z2 composite
            comparison_data: Comparison result from CompositeComparisonService
            
        Returns:
            Dict with AI analysis including:
            - summary: Brief summary of changes
            - significant_changes: List of significant changes with context
            - recommendations: Recommendations based on changes
            - risk_assessment: Risk level and explanation
        """
        if not self.client:
            return {
                "ai_analysis_available": False,
                "message": "OpenAI API key not configured. AI analysis unavailable."
            }
        
        try:
            # Prepare component data for AI
            z1_components = [
                {
                    "name": c.component_name,
                    "cas": c.cas_number,
                    "percentage": c.percentage
                }
                for c in z1_composite.components
            ]
            
            z2_components = [
                {
                    "name": c.component_name,
                    "cas": c.cas_number,
                    "percentage": c.percentage
                }
                for c in z2_composite.components
            ]
            
            # Build prompt
            prompt = self._build_analysis_prompt(
                z1_components,
                z2_components,
                comparison_data
            )
            
            # Call OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert chemist and quality control specialist analyzing 
chemical composition changes between provisional (Z1) and definitive (Z2) composites.

Your task is to:
1. Identify significant changes that may affect product quality or regulatory compliance
2. Explain the implications of component additions, removals, or percentage changes
3. Assess potential risks (regulatory, safety, quality)
4. Provide actionable recommendations

Be concise but thorough. Focus on:
- Regulatory compliance (REACH, IFRA, allergen concerns)
- Safety implications (new components, significant percentage changes)
- Quality consistency (major variations in key components)
- Recommendations for further action if needed"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent, factual analysis
                max_tokens=1000
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Parse AI response into structured format
            analysis = self._parse_ai_response(ai_response, comparison_data)
            
            return {
                "ai_analysis_available": True,
                "summary": analysis.get("summary", ""),
                "significant_changes": analysis.get("significant_changes", []),
                "recommendations": analysis.get("recommendations", []),
                "risk_assessment": analysis.get("risk_assessment", {}),
                "raw_analysis": ai_response
            }
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}", exc_info=True)
            return {
                "ai_analysis_available": False,
                "error": str(e),
                "message": "AI analysis failed. Basic comparison data is still available."
            }
    
    def _build_analysis_prompt(
        self,
        z1_components: List[Dict],
        z2_components: List[Dict],
        comparison_data: Dict[str, Any]
    ) -> str:
        """Build the prompt for AI analysis."""
        
        added = comparison_data.get("components_added", [])
        removed = comparison_data.get("components_removed", [])
        changed = comparison_data.get("components_changed", [])
        
        prompt = f"""Analyze the changes between a provisional composite (Z1) and a definitive laboratory composite (Z2).

Z1 COMPOSITE (Provisional - from supplier documents):
{self._format_components(z1_components)}

Z2 COMPOSITE (Definitive - from laboratory analysis):
{self._format_components(z2_components)}

CHANGES DETECTED:
"""
        
        if added:
            prompt += f"\nADDED COMPONENTS ({len(added)}):\n"
            for comp in added:
                prompt += f"  - {comp.get('component_name', 'Unknown')} (CAS: {comp.get('cas_number', 'N/A')}): {comp.get('new_percentage', 0)}%\n"
        
        if removed:
            prompt += f"\nREMOVED COMPONENTS ({len(removed)}):\n"
            for comp in removed:
                prompt += f"  - {comp.get('component_name', 'Unknown')} (CAS: {comp.get('cas_number', 'N/A')}): was {comp.get('old_percentage', 0)}%\n"
        
        if changed:
            prompt += f"\nCHANGED COMPONENTS ({len(changed)}):\n"
            for comp in changed:
                change_pct = comp.get('change_percent', 0)
                prompt += f"  - {comp.get('component_name', 'Unknown')} (CAS: {comp.get('cas_number', 'N/A')}): "
                prompt += f"{comp.get('old_percentage', 0)}% → {comp.get('new_percentage', 0)}% "
                prompt += f"({change_pct:+.1f}% change)\n"
        
        prompt += """
Please provide:
1. A brief summary of the key changes
2. Identification of any significant changes (>5% variation or new/removed components) with context
3. Risk assessment (LOW/MEDIUM/HIGH) with explanation
4. Recommendations for action (if any)

Format your response as JSON with these keys:
- summary: string
- significant_changes: array of {component_name, cas_number, change_description, implication}
- risk_assessment: {level: "LOW|MEDIUM|HIGH", explanation: string}
- recommendations: array of strings
"""
        
        return prompt
    
    def _format_components(self, components: List[Dict]) -> str:
        """Format components list for prompt."""
        if not components:
            return "  (No components)"
        
        formatted = ""
        for comp in components[:20]:  # Limit to first 20 to avoid token limits
            formatted += f"  - {comp['name']} (CAS: {comp['cas']}): {comp['percentage']}%\n"
        
        if len(components) > 20:
            formatted += f"  ... and {len(components) - 20} more components\n"
        
        return formatted
    
    def _parse_ai_response(self, response: str, comparison_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse AI response into structured format."""
        import json
        import re
        
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                return parsed
            except json.JSONDecodeError:
                pass
        
        # Fallback: return structured response from text
        return {
            "summary": response[:500] if len(response) > 500 else response,
            "significant_changes": [],
            "recommendations": [],
            "risk_assessment": {
                "level": "UNKNOWN",
                "explanation": "Could not parse AI response"
            }
        }


