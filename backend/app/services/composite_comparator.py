from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.models.composite import Composite, CompositeComponent
from app.schemas.composite import ComponentComparison, CompositeCompareResponse
from app.core.config import settings


class CompositeComparator:
    """Service for comparing composite versions"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def compare_composites(
        self,
        old_composite_id: int,
        new_composite_id: int
    ) -> CompositeCompareResponse:
        """
        Compare two composite versions
        
        Args:
            old_composite_id: ID of the old composite
            new_composite_id: ID of the new composite
            
        Returns:
            CompositeCompareResponse with comparison details
        """
        # Get composites
        old_composite = self.db.query(Composite).filter(
            Composite.id == old_composite_id
        ).first()
        new_composite = self.db.query(Composite).filter(
            Composite.id == new_composite_id
        ).first()
        
        if not old_composite or not new_composite:
            raise ValueError("One or both composites not found")
        
        # Create component maps
        old_components = self._create_component_map(old_composite.components)
        new_components = self._create_component_map(new_composite.components)
        
        # Find changes
        components_added = []
        components_removed = []
        components_changed = []
        
        # Check for removed components
        for key, old_comp in old_components.items():
            if key not in new_components:
                components_removed.append(ComponentComparison(
                    component_name=old_comp.component_name,
                    cas_number=old_comp.cas_number,
                    old_percentage=old_comp.percentage,
                    new_percentage=None,
                    change=-old_comp.percentage,
                    change_percent=-100.0
                ))
        
        # Check for added and changed components
        for key, new_comp in new_components.items():
            if key not in old_components:
                # Added component
                components_added.append(ComponentComparison(
                    component_name=new_comp.component_name,
                    cas_number=new_comp.cas_number,
                    old_percentage=None,
                    new_percentage=new_comp.percentage,
                    change=new_comp.percentage,
                    change_percent=None
                ))
            else:
                # Potentially changed component
                old_comp = old_components[key]
                percentage_change = new_comp.percentage - old_comp.percentage
                
                if abs(percentage_change) > 0.01:  # More than 0.01% change
                    change_percent = (percentage_change / old_comp.percentage * 100) if old_comp.percentage > 0 else 0
                    
                    components_changed.append(ComponentComparison(
                        component_name=new_comp.component_name,
                        cas_number=new_comp.cas_number,
                        old_percentage=old_comp.percentage,
                        new_percentage=new_comp.percentage,
                        change=percentage_change,
                        change_percent=change_percent
                    ))
        
        # Calculate total change score
        total_change_score = sum(abs(c.change) for c in components_changed)
        total_change_score += sum(abs(c.change) for c in components_added)
        total_change_score += sum(abs(c.change) for c in components_removed)
        
        # Determine if changes are significant
        significant_changes = total_change_score >= settings.COMPOSITE_THRESHOLD_PERCENT
        
        return CompositeCompareResponse(
            old_composite_id=old_composite_id,
            new_composite_id=new_composite_id,
            old_version=old_composite.version,
            new_version=new_composite.version,
            components_added=components_added,
            components_removed=components_removed,
            components_changed=components_changed,
            significant_changes=significant_changes,
            total_change_score=round(total_change_score, 2)
        )
    
    def _create_component_map(self, components: List[CompositeComponent]) -> Dict[str, CompositeComponent]:
        """
        Create a map of components keyed by CAS or name
        
        Returns:
            Dictionary mapping component key to CompositeComponent
        """
        component_map = {}
        
        for component in components:
            # Use CAS number as key if available, otherwise use normalized name
            if component.cas_number:
                key = f"cas_{component.cas_number}"
            else:
                key = f"name_{component.component_name.lower().strip()}"
            
            component_map[key] = component
        
        return component_map
    
    def get_composite_history(self, material_id: int) -> List[Composite]:
        """
        Get all composite versions for a material, ordered by version
        
        Args:
            material_id: ID of the material
            
        Returns:
            List of composites ordered by version (newest first)
        """
        return self.db.query(Composite).filter(
            Composite.material_id == material_id
        ).order_by(Composite.version.desc()).all()






