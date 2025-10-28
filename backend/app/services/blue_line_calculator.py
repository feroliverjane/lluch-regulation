from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from app.models.material import Material
from app.models.blue_line import BlueLine, BlueLineMaterialType
from app.models.blue_line_field_logic import BlueLineFieldLogic
from app.models.approval_workflow import ApprovalWorkflow, WorkflowStatus
from app.models.composite import Composite, CompositeStatus
from app.core.config import settings
from app.integrations.erp_adapter import ERPAdapter

logger = logging.getLogger(__name__)


class BlueLineCalculator:
    """Service for calculating Blue Line records based on homologation data"""
    
    def __init__(self, db: Session):
        self.db = db
        self.erp_adapter = ERPAdapter()
    
    async def calculate_blue_line(
        self,
        material_id: int,
        supplier_code: str,
        force_recalculate: bool = False
    ) -> Optional[BlueLine]:
        """
        Main entry point for Blue Line calculation
        
        Args:
            material_id: Material ID
            supplier_code: Supplier code
            force_recalculate: Force recalculation even if exists
            
        Returns:
            BlueLine object or None if not eligible
        """
        logger.info(f"Starting Blue Line calculation for material {material_id}, supplier {supplier_code}")
        
        # Get material
        material = self.db.query(Material).filter(Material.id == material_id).first()
        if not material:
            logger.error(f"Material {material_id} not found")
            return None
        
        # Check eligibility
        is_eligible, eligibility_details = await self.check_eligibility(material_id, supplier_code)
        
        if not is_eligible:
            logger.info(f"Material {material_id} not eligible for Blue Line: {eligibility_details}")
            return None
        
        # Check if Blue Line already exists
        existing_blue_line = self.db.query(BlueLine).filter(
            BlueLine.material_id == material_id,
            BlueLine.supplier_code == supplier_code
        ).first()
        
        if existing_blue_line and not force_recalculate:
            logger.info(f"Blue Line already exists for material {material_id}, supplier {supplier_code}")
            return existing_blue_line
        
        # Determine material type (Z001 or Z002)
        material_type = self.determine_material_type(material)
        
        # Aggregate homologation records
        homologation_data = self.aggregate_homologation_records(material_id, supplier_code)
        
        # Get active approved composites for this material
        approved_composites = self.db.query(Composite).filter(
            Composite.material_id == material_id,
            Composite.status == CompositeStatus.APPROVED
        ).order_by(Composite.version.desc()).all()
        
        # Calculate 446 fields using field logic
        blue_line_data = await self.calculate_all_fields(
            material=material,
            supplier_code=supplier_code,
            material_type=material_type,
            composites=approved_composites,
            homologation_data=homologation_data
        )
        
        # Create or update Blue Line
        if existing_blue_line:
            existing_blue_line.blue_line_data = blue_line_data
            existing_blue_line.material_type = material_type
            existing_blue_line.calculated_at = datetime.now()
            existing_blue_line.calculation_metadata = {
                "last_calculation": datetime.now().isoformat(),
                "eligibility_details": eligibility_details,
                "composites_used": [c.id for c in approved_composites],
                "homologation_records_count": len(homologation_data) if homologation_data else 0
            }
            blue_line = existing_blue_line
        else:
            blue_line = BlueLine(
                material_id=material_id,
                supplier_code=supplier_code,
                blue_line_data=blue_line_data,
                material_type=material_type,
                calculation_metadata={
                    "created": datetime.now().isoformat(),
                    "eligibility_details": eligibility_details,
                    "composites_used": [c.id for c in approved_composites],
                    "homologation_records_count": len(homologation_data) if homologation_data else 0
                }
            )
            self.db.add(blue_line)
        
        self.db.commit()
        self.db.refresh(blue_line)
        
        # Update material eligibility flag
        material.is_blue_line_eligible = True
        self.db.commit()
        
        logger.info(f"Blue Line calculated successfully for material {material_id}, supplier {supplier_code}")
        return blue_line
    
    async def check_eligibility(
        self,
        material_id: int,
        supplier_code: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if material-supplier pair is eligible for Blue Line creation
        
        Eligibility rules:
        1. Must have APC or APR in Regulatory section
        2. Must NOT have REJ in Technical section
        3. Must have purchase in last 3 years
        
        Returns:
            Tuple of (is_eligible, details_dict)
        """
        material = self.db.query(Material).filter(Material.id == material_id).first()
        if not material:
            return False, {"error": "Material not found"}
        
        details = {
            "has_purchase_history": False,
            "regulatory_status_ok": False,
            "technical_status_ok": False,
            "reasons": []
        }
        
        # Check purchase history (last 3 years)
        lookback_date = datetime.now() - timedelta(days=365 * settings.BLUE_LINE_PURCHASE_LOOKBACK_YEARS)
        
        # Try to get from ERP
        purchase_history = await self.erp_adapter.get_purchase_history_last_n_years(
            material.reference_code,
            settings.BLUE_LINE_PURCHASE_LOOKBACK_YEARS
        )
        
        # If ERP enabled and returns data
        if purchase_history is not None:
            details["has_purchase_history"] = len(purchase_history) > 0
            if details["has_purchase_history"]:
                details["purchase_count"] = len(purchase_history)
        else:
            # Fallback: check material.last_purchase_date
            if material.last_purchase_date and material.last_purchase_date >= lookback_date:
                details["has_purchase_history"] = True
        
        if not details["has_purchase_history"]:
            details["reasons"].append(f"No purchases in last {settings.BLUE_LINE_PURCHASE_LOOKBACK_YEARS} years")
        
        # Check approval workflow states
        workflows = self.db.query(ApprovalWorkflow).join(
            Composite, ApprovalWorkflow.composite_id == Composite.id
        ).filter(
            Composite.material_id == material_id
        ).all()
        
        # Check for APC or APR in Regulatory
        has_regulatory_approval = False
        for workflow in workflows:
            if workflow.regulatory_status in ["APC", "APR"]:
                has_regulatory_approval = True
                break
            # Also check main status for backward compatibility
            if workflow.status in [WorkflowStatus.APC, WorkflowStatus.APR]:
                has_regulatory_approval = True
                break
        
        details["regulatory_status_ok"] = has_regulatory_approval
        if not has_regulatory_approval:
            details["reasons"].append("No APC or APR approval in Regulatory section")
        
        # Check for NO REJ in Technical
        has_technical_rejection = False
        for workflow in workflows:
            if workflow.technical_status == "REJ":
                has_technical_rejection = True
                break
            # Also check main status
            if workflow.status == WorkflowStatus.REJ and workflow.section == "Technical":
                has_technical_rejection = True
                break
        
        details["technical_status_ok"] = not has_technical_rejection
        if has_technical_rejection:
            details["reasons"].append("Has REJ (rejection) in Technical section")
        
        # Overall eligibility
        is_eligible = (
            details["has_purchase_history"] and
            details["regulatory_status_ok"] and
            details["technical_status_ok"]
        )
        
        return is_eligible, details
    
    def determine_material_type(self, material: Material) -> BlueLineMaterialType:
        """
        Determine if material is Z001 (provisional) or Z002 (homologated)
        
        Logic:
        - Z002 if has approved composite with origin=LAB (analyzed by Lluch)
        - Z001 otherwise (provisional/worst case from supplier)
        """
        # Check for LAB composites
        lab_composite = self.db.query(Composite).filter(
            Composite.material_id == material.id,
            Composite.status == CompositeStatus.APPROVED,
            Composite.origin == "LAB"
        ).first()
        
        if lab_composite:
            return BlueLineMaterialType.Z002
        else:
            return BlueLineMaterialType.Z001
    
    def aggregate_homologation_records(
        self,
        material_id: int,
        supplier_code: str
    ) -> List[Dict[str, Any]]:
        """
        Aggregate homologation records, excluding CAN, REJ, EXP states
        
        Returns:
            List of valid homologation workflow data
        """
        excluded_states = [WorkflowStatus.CAN, WorkflowStatus.REJ, WorkflowStatus.EXP]
        
        workflows = self.db.query(ApprovalWorkflow).join(
            Composite, ApprovalWorkflow.composite_id == Composite.id
        ).join(
            Material, Composite.material_id == Material.id
        ).filter(
            Material.id == material_id,
            Material.supplier_code == supplier_code,
            ~ApprovalWorkflow.status.in_(excluded_states)
        ).all()
        
        homologation_data = []
        for workflow in workflows:
            homologation_data.append({
                "workflow_id": workflow.id,
                "composite_id": workflow.composite_id,
                "status": workflow.status.value if hasattr(workflow.status, 'value') else workflow.status,
                "regulatory_status": workflow.regulatory_status,
                "technical_status": workflow.technical_status,
                "reviewed_at": workflow.reviewed_at.isoformat() if workflow.reviewed_at else None
            })
        
        return homologation_data
    
    async def calculate_all_fields(
        self,
        material: Material,
        supplier_code: str,
        material_type: BlueLineMaterialType,
        composites: List[Composite],
        homologation_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate all 446 Blue Line fields using configured field logic
        
        Returns:
            Dictionary with all field values
        """
        # Get all active field logics for this material type
        field_logics = self.db.query(BlueLineFieldLogic).filter(
            BlueLineFieldLogic.is_active == True,
            (BlueLineFieldLogic.material_type_filter == "ALL") |
            (BlueLineFieldLogic.material_type_filter == material_type.value)
        ).order_by(BlueLineFieldLogic.priority).all()
        
        blue_line_data = {}
        
        # Apply each field logic
        for field_logic in field_logics:
            try:
                field_value = await self.apply_field_logic(
                    field_logic=field_logic,
                    material=material,
                    supplier_code=supplier_code,
                    composites=composites,
                    homologation_data=homologation_data,
                    current_data=blue_line_data
                )
                blue_line_data[field_logic.field_name] = field_value
            except Exception as e:
                logger.error(f"Error applying field logic for {field_logic.field_name}: {e}")
                blue_line_data[field_logic.field_name] = None
        
        return blue_line_data
    
    async def apply_field_logic(
        self,
        field_logic: BlueLineFieldLogic,
        material: Material,
        supplier_code: str,
        composites: List[Composite],
        homologation_data: List[Dict[str, Any]],
        current_data: Dict[str, Any]
    ) -> Any:
        """
        Apply a single field's calculation logic
        
        This is a simplified implementation. In production, you would:
        1. Parse the logic_expression JSON
        2. Execute the logic (possibly using a rules engine)
        3. Return the calculated value
        
        Example logic_expression formats:
        - {"source": "material.name"} -> Return material.name
        - {"source": "material.supplier"} -> Return material.supplier
        - {"fixed_value": "LLUCH"} -> Return "LLUCH"
        - {"calculation": {"type": "count", "source": "composites"}} -> Return len(composites)
        """
        logic = field_logic.logic_expression
        
        # Handle different logic types
        if "source" in logic:
            source = logic["source"]
            
            # Parse source (e.g., "material.name")
            if source.startswith("material."):
                attr_name = source.split(".")[1]
                return getattr(material, attr_name, None)
            
            elif source.startswith("composite.") and composites:
                # Use latest composite
                latest_composite = composites[0] if composites else None
                if latest_composite:
                    attr_name = source.split(".")[1]
                    return getattr(latest_composite, attr_name, None)
            
            elif source == "supplier_code":
                return supplier_code
        
        elif "fixed_value" in logic:
            return logic["fixed_value"]
        
        elif "calculation" in logic:
            calc = logic["calculation"]
            calc_type = calc.get("type")
            
            if calc_type == "count":
                source = calc.get("source")
                if source == "composites":
                    return len(composites)
                elif source == "homologation_records":
                    return len(homologation_data)
            
            elif calc_type == "list":
                source = calc.get("source")
                if source == "composite.components" and composites:
                    latest_composite = composites[0]
                    return [
                        {
                            "name": c.component_name,
                            "cas": c.cas_number,
                            "percentage": c.percentage
                        }
                        for c in latest_composite.components
                    ]
        
        # Default: return None if logic not recognized
        return None
    
    async def handle_single_provider_rejection(
        self,
        material_id: int,
        supplier_code: str
    ) -> bool:
        """
        Handle case where single provider's homologation is rejected/cancelled/expired
        Should delete or empty the Blue Line
        
        Returns:
            True if Blue Line was deleted, False otherwise
        """
        # Check if this is the only provider for this material
        all_suppliers = self.db.query(Material.supplier_code).filter(
            Material.id == material_id,
            Material.supplier_code.isnot(None)
        ).distinct().all()
        
        if len(all_suppliers) == 1:
            # This is the only supplier, check if all workflows are rejected
            workflows = self.db.query(ApprovalWorkflow).join(
                Composite, ApprovalWorkflow.composite_id == Composite.id
            ).filter(
                Composite.material_id == material_id
            ).all()
            
            all_rejected = all(
                workflow.status in [WorkflowStatus.CAN, WorkflowStatus.REJ, WorkflowStatus.EXP]
                for workflow in workflows
            )
            
            if all_rejected:
                # Delete Blue Line
                blue_line = self.db.query(BlueLine).filter(
                    BlueLine.material_id == material_id,
                    BlueLine.supplier_code == supplier_code
                ).first()
                
                if blue_line:
                    self.db.delete(blue_line)
                    self.db.commit()
                    logger.info(f"Deleted Blue Line for material {material_id}, supplier {supplier_code} (single provider rejection)")
                    return True
        
        return False

