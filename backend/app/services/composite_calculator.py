from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from collections import defaultdict
import statistics

from app.models.chromatographic_analysis import ChromatographicAnalysis
from app.models.composite import Composite, CompositeComponent, CompositeOrigin, CompositeStatus
from app.models.material import Material


class CompositeCalculator:
    """Service for calculating composites from chromatographic analyses"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_from_lab_analyses(
        self,
        material_id: int,
        analysis_ids: Optional[List[int]] = None,
        notes: Optional[str] = None
    ) -> Composite:
        """
        Calculate composite from laboratory chromatographic analyses
        
        Args:
            material_id: ID of the material
            analysis_ids: Specific analysis IDs to use (None = use all)
            notes: Optional notes for the composite
            
        Returns:
            Calculated Composite object (not yet saved to DB)
        """
        # Get material
        material = self.db.query(Material).filter(Material.id == material_id).first()
        if not material:
            raise ValueError(f"Material {material_id} not found")
        
        # Get analyses
        query = self.db.query(ChromatographicAnalysis).filter(
            ChromatographicAnalysis.material_id == material_id,
            ChromatographicAnalysis.is_processed == 1
        )
        
        if analysis_ids:
            query = query.filter(ChromatographicAnalysis.id.in_(analysis_ids))
        
        analyses = query.all()
        
        if not analyses:
            raise ValueError(f"No processed analyses found for material {material_id}")
        
        # Aggregate components from all analyses
        aggregated = self._aggregate_analyses(analyses)
        
        # Get next version number
        max_version = self.db.query(Composite.version).filter(
            Composite.material_id == material_id
        ).order_by(Composite.version.desc()).first()
        
        next_version = (max_version[0] + 1) if max_version else 1
        
        # Create composite
        composite = Composite(
            material_id=material_id,
            version=next_version,
            origin=CompositeOrigin.LAB,
            status=CompositeStatus.DRAFT,
            notes=notes,
            composite_metadata={
                'analysis_ids': [a.id for a in analyses],
                'analysis_count': len(analyses),
                'batches': [a.batch_number for a in analyses if a.batch_number],
                'suppliers': list(set(a.supplier for a in analyses if a.supplier)),
                'calculation_method': 'weighted_average'
            }
        )
        
        # Create components
        composite.components = [
            CompositeComponent(**comp_data)
            for comp_data in aggregated
        ]
        
        return composite
    
    def _aggregate_analyses(self, analyses: List[ChromatographicAnalysis]) -> List[Dict[str, Any]]:
        """
        Aggregate multiple chromatographic analyses using weighted average
        
        Returns:
            List of component dictionaries
        """
        # Organize components by name (and CAS if available)
        component_data = defaultdict(lambda: {
            'percentages': [],
            'weights': [],
            'cas_numbers': set(),
            'types': []
        })
        
        total_weight = sum(a.weight for a in analyses)
        
        for analysis in analyses:
            if not analysis.parsed_data or 'components' not in analysis.parsed_data:
                continue
            
            for component in analysis.parsed_data['components']:
                key = self._get_component_key(component)
                
                component_data[key]['percentages'].append(component['percentage'])
                component_data[key]['weights'].append(analysis.weight)
                
                if component.get('cas_number'):
                    component_data[key]['cas_numbers'].add(component['cas_number'])
                
                component_data[key]['types'].append(component.get('component_type', 'COMPONENT'))
                component_data[key]['name'] = component['component_name']
        
        # Calculate weighted averages
        aggregated_components = []
        
        for key, data in component_data.items():
            # Weighted average
            weighted_percentage = sum(
                p * w for p, w in zip(data['percentages'], data['weights'])
            ) / sum(data['weights'])
            
            # Calculate confidence level based on consistency across analyses
            if len(data['percentages']) > 1:
                std_dev = statistics.stdev(data['percentages'])
                mean = statistics.mean(data['percentages'])
                coefficient_of_variation = (std_dev / mean * 100) if mean > 0 else 100
                # Higher consistency = higher confidence
                confidence = max(0, 100 - coefficient_of_variation * 2)
            else:
                confidence = 70.0  # Default for single analysis
            
            # Determine CAS number (use most common, or first if tie)
            cas_number = list(data['cas_numbers'])[0] if data['cas_numbers'] else None
            
            # Determine type (use most common)
            component_type = max(set(data['types']), key=data['types'].count) if data['types'] else 'COMPONENT'
            
            aggregated_components.append({
                'component_name': data['name'],
                'cas_number': cas_number,
                'percentage': round(weighted_percentage, 4),
                'component_type': component_type,
                'confidence_level': round(confidence, 2),
                'notes': f'Aggregated from {len(data["percentages"])} analyses'
            })
        
        # Sort by percentage (descending)
        aggregated_components.sort(key=lambda x: x['percentage'], reverse=True)
        
        # Normalize to 100%
        total = sum(c['percentage'] for c in aggregated_components)
        if total > 0:
            normalization_factor = 100.0 / total
            for component in aggregated_components:
                component['percentage'] = round(component['percentage'] * normalization_factor, 4)
        
        return aggregated_components
    
    def _get_component_key(self, component: Dict[str, Any]) -> str:
        """
        Generate a unique key for a component
        Prioritize CAS number, fall back to name
        """
        cas = component.get('cas_number')
        name = component.get('component_name', '').lower().strip()
        
        if cas:
            return f"cas_{cas}"
        return f"name_{name}"
    
    def calculate_from_documents(
        self,
        material_id: int,
        components_data: List[Dict[str, Any]],
        notes: Optional[str] = None
    ) -> Composite:
        """
        Calculate composite from manual/document data
        
        Args:
            material_id: ID of the material
            components_data: List of component dictionaries
            notes: Optional notes
            
        Returns:
            Composite object
        """
        # Get material
        material = self.db.query(Material).filter(Material.id == material_id).first()
        if not material:
            raise ValueError(f"Material {material_id} not found")
        
        # Get next version
        max_version = self.db.query(Composite.version).filter(
            Composite.material_id == material_id
        ).order_by(Composite.version.desc()).first()
        
        next_version = (max_version[0] + 1) if max_version else 1
        
        # Create composite
        composite = Composite(
            material_id=material_id,
            version=next_version,
            origin=CompositeOrigin.CALCULATED,
            status=CompositeStatus.DRAFT,
            notes=notes,
            composite_metadata={
                'source': 'manual_entry',
                'calculation_method': 'document_based'
            }
        )
        
        # Normalize percentages
        total = sum(c['percentage'] for c in components_data)
        normalization_factor = 100.0 / total if total > 0 else 1.0
        
        # Create components
        composite.components = [
            CompositeComponent(
                component_name=comp['component_name'],
                cas_number=comp.get('cas_number'),
                percentage=round(comp['percentage'] * normalization_factor, 4),
                component_type=comp.get('component_type', 'COMPONENT'),
                notes=comp.get('notes')
            )
            for comp in components_data
        ]
        
        return composite

