"""
Composite Comparison Service

Service for comparing two composites and calculating average/merged composites.
Used for Z1 composite updates and validation.
"""

import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.models.composite import Composite, CompositeComponent, CompositeType
from app.schemas.composite import ComponentComparison, CompositeCompareResponse

logger = logging.getLogger(__name__)


class CompositeComparisonService:
    """
    Service for comparing and merging composites.
    Handles Z1 composite updates by averaging with new supplier data.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.significant_change_threshold = 5.0  # 5% change is significant
    
    def compare_composites(
        self,
        composite_a_id: int,
        composite_b_id: int
    ) -> Dict[str, Any]:
        """
        Compare two composites and identify differences.
        
        Args:
            composite_a_id: First composite ID
            composite_b_id: Second composite ID
            
        Returns:
            Comparison result dict
        """
        composite_a = self.db.query(Composite).filter(Composite.id == composite_a_id).first()
        composite_b = self.db.query(Composite).filter(Composite.id == composite_b_id).first()
        
        if not composite_a or not composite_b:
            raise ValueError("One or both composites not found")
        
        # Build component maps by CAS number
        components_a = {c.cas_number: c for c in composite_a.components}
        components_b = {c.cas_number: c for c in composite_b.components}
        
        # Find additions, removals, and changes
        added = []
        removed = []
        changed = []
        
        # Check for new components in B
        for cas, component_b in components_b.items():
            if cas not in components_a:
                added.append(ComponentComparison(
                    component_name=component_b.component_name,
                    cas_number=cas,
                    old_percentage=None,
                    new_percentage=component_b.percentage,
                    change=component_b.percentage,
                    change_percent=None
                ))
        
        # Check for removed components
        for cas, component_a in components_a.items():
            if cas not in components_b:
                removed.append(ComponentComparison(
                    component_name=component_a.component_name,
                    cas_number=cas,
                    old_percentage=component_a.percentage,
                    new_percentage=None,
                    change=-component_a.percentage,
                    change_percent=None
                ))
        
        # Check for changed components
        for cas, component_a in components_a.items():
            if cas in components_b:
                component_b = components_b[cas]
                change = component_b.percentage - component_a.percentage
                change_percent = (change / component_a.percentage * 100) if component_a.percentage > 0 else 0
                
                if abs(change) > 0.01:  # Only if changed
                    changed.append(ComponentComparison(
                        component_name=component_a.component_name,
                        cas_number=cas,
                        old_percentage=component_a.percentage,
                        new_percentage=component_b.percentage,
                        change=change,
                        change_percent=change_percent
                    ))
        
        # Calculate significance
        significant_changes = any(
            abs(c.change) >= self.significant_change_threshold for c in changed
        )
        
        # Calculate total change score
        total_change_score = sum(abs(c.change) for c in changed)
        total_change_score += sum(c.change for c in added)
        total_change_score += sum(abs(c.change) for c in removed)
        
        # Calculate match score (0-100)
        match_score = max(0, 100 - total_change_score)
        
        return {
            "composite_a_id": composite_a_id,
            "composite_b_id": composite_b_id,
            "composite_a_version": composite_a.version,
            "composite_b_version": composite_b.version,
            "components_added": [c.dict() for c in added],
            "components_removed": [c.dict() for c in removed],
            "components_changed": [c.dict() for c in changed],
            "significant_changes": significant_changes,
            "total_change_score": total_change_score,
            "match_score": match_score
        }
    
    def calculate_average_composite(
        self,
        composite_a_id: int,
        composite_b_id: int,
        target_material_id: int
    ) -> Composite:
        """
        Calculate average composite from two composites.
        Used for updating Z1 composites with new supplier data.
        
        Args:
            composite_a_id: Existing composite ID (Z1)
            composite_b_id: New composite ID (from new questionnaire)
            target_material_id: Material ID for new composite
            
        Returns:
            New averaged composite (not yet committed)
        """
        composite_a = self.db.query(Composite).filter(Composite.id == composite_a_id).first()
        composite_b = self.db.query(Composite).filter(Composite.id == composite_b_id).first()
        
        if not composite_a or not composite_b:
            raise ValueError("One or both composites not found")
        
        # Build component maps
        components_a = {c.cas_number: c for c in composite_a.components}
        components_b = {c.cas_number: c for c in composite_b.components}
        
        # Calculate averaged components
        averaged_components = []
        all_cas_numbers = set(components_a.keys()) | set(components_b.keys())
        
        for cas in all_cas_numbers:
            comp_a = components_a.get(cas)
            comp_b = components_b.get(cas)
            
            if comp_a and comp_b:
                # Average the percentages
                avg_percentage = (comp_a.percentage + comp_b.percentage) / 2
                component_name = comp_a.component_name  # Prefer A's name
                confidence = (comp_a.confidence_level + comp_b.confidence_level) / 2 if (comp_a.confidence_level and comp_b.confidence_level) else None
            elif comp_a:
                # Only in A, keep as is
                avg_percentage = comp_a.percentage
                component_name = comp_a.component_name
                confidence = comp_a.confidence_level
            else:
                # Only in B, keep as is
                avg_percentage = comp_b.percentage
                component_name = comp_b.component_name
                confidence = comp_b.confidence_level
            
            averaged_components.append({
                'cas_number': cas,
                'component_name': component_name,
                'percentage': avg_percentage,
                'confidence_level': confidence
            })
        
        # Normalize percentages to sum to 100
        total_percentage = sum(c['percentage'] for c in averaged_components)
        if total_percentage > 0:
            for comp in averaged_components:
                comp['percentage'] = (comp['percentage'] / total_percentage) * 100
        
        # Determine next version
        next_version = max(composite_a.version, composite_b.version) + 1
        
        # Create new composite
        new_composite = Composite(
            material_id=target_material_id,
            version=next_version,
            origin=composite_a.origin,  # Keep origin from A
            composite_type=CompositeType.Z1,  # Averaged composite is still Z1
            status=composite_a.status,
            composite_metadata={
                "averaged_from": [composite_a_id, composite_b_id],
                "source_a_version": composite_a.version,
                "source_b_version": composite_b.version,
                "averaging_method": "simple_average"
            },
            notes=f"Averaged from composite {composite_a_id} (v{composite_a.version}) and {composite_b_id} (v{composite_b.version})"
        )
        
        # Add components
        for comp_data in averaged_components:
            component = CompositeComponent(
                cas_number=comp_data['cas_number'],
                component_name=comp_data['component_name'],
                percentage=comp_data['percentage'],
                confidence_level=comp_data['confidence_level']
            )
            new_composite.components.append(component)
        
        logger.info(
            f"Created averaged composite with {len(averaged_components)} components "
            f"from composites {composite_a_id} and {composite_b_id}"
        )
        
        return new_composite
    
    def calculate_weighted_average_composite(
        self,
        composite_ids: List[int],
        weights: List[float],
        target_material_id: int
    ) -> Composite:
        """
        Calculate weighted average composite from multiple composites.
        
        Args:
            composite_ids: List of composite IDs
            weights: List of weights (should sum to 1.0)
            target_material_id: Material ID for new composite
            
        Returns:
            New weighted average composite
        """
        if len(composite_ids) != len(weights):
            raise ValueError("Number of composites must match number of weights")
        
        if abs(sum(weights) - 1.0) > 0.01:
            raise ValueError("Weights must sum to 1.0")
        
        # Get all composites
        composites = self.db.query(Composite).filter(
            Composite.id.in_(composite_ids)
        ).all()
        
        if len(composites) != len(composite_ids):
            raise ValueError("One or more composites not found")
        
        # Build weighted component map
        weighted_components = {}
        
        for composite, weight in zip(composites, weights):
            for component in composite.components:
                cas = component.cas_number
                
                if cas not in weighted_components:
                    weighted_components[cas] = {
                        'cas_number': cas,
                        'component_name': component.component_name,
                        'percentage': 0,
                        'confidence_level': 0,
                        'count': 0
                    }
                
                weighted_components[cas]['percentage'] += component.percentage * weight
                if component.confidence_level:
                    weighted_components[cas]['confidence_level'] += component.confidence_level * weight
                weighted_components[cas]['count'] += 1
        
        # Normalize percentages
        components_list = list(weighted_components.values())
        total_percentage = sum(c['percentage'] for c in components_list)
        if total_percentage > 0:
            for comp in components_list:
                comp['percentage'] = (comp['percentage'] / total_percentage) * 100
        
        # Create new composite
        max_version = max(c.version for c in composites)
        new_composite = Composite(
            material_id=target_material_id,
            version=max_version + 1,
            origin=composites[0].origin,
            composite_type=CompositeType.Z1,
            composite_metadata={
                "averaged_from": composite_ids,
                "weights": weights,
                "averaging_method": "weighted_average"
            },
            notes=f"Weighted average from {len(composites)} composites"
        )
        
        for comp_data in components_list:
            component = CompositeComponent(
                cas_number=comp_data['cas_number'],
                component_name=comp_data['component_name'],
                percentage=comp_data['percentage'],
                confidence_level=comp_data['confidence_level'] if comp_data['confidence_level'] > 0 else None
            )
            new_composite.components.append(component)
        
        return new_composite












