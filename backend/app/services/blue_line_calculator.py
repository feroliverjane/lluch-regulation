from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from app.models.material import Material
from app.models.blue_line import BlueLine, BlueLineMaterialType
from app.models.blue_line_field_logic import BlueLineFieldLogic
from app.models.approval_workflow import ApprovalWorkflow, WorkflowStatus
from app.models.composite import Composite, CompositeStatus, CompositeOrigin
from app.models.questionnaire_template import QuestionnaireTemplate, TemplateType
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
        force_recalculate: bool = False
    ) -> Optional[BlueLine]:
        """
        Main entry point for Blue Line calculation
        
        Args:
            material_id: Material ID
            force_recalculate: Force recalculation even if exists
            
        Returns:
            BlueLine object or None if not eligible
        """
        logger.info(f"Starting Blue Line calculation for material {material_id}")
        
        # Get material
        material = self.db.query(Material).filter(Material.id == material_id).first()
        if not material:
            logger.error(f"Material {material_id} not found")
            return None
        
        # Check eligibility (no longer needs supplier_code)
        is_eligible, eligibility_details = await self.check_eligibility(material_id)
        
        if not is_eligible:
            logger.info(f"Material {material_id} not eligible for Blue Line: {eligibility_details}")
            return None
        
        # Check if Blue Line already exists for this material
        existing_blue_line = self.db.query(BlueLine).filter(
            BlueLine.material_id == material_id
        ).first()
        
        if existing_blue_line and not force_recalculate:
            logger.info(f"Blue Line already exists for material {material_id}")
            return existing_blue_line
        
        # Determine material type (Z001 or Z002)
        material_type = self.determine_material_type(material)
        
        # Aggregate homologation records (now for all suppliers of this material)
        homologation_data = self.aggregate_homologation_records(material_id)
        
        # Get active approved composites for this material
        approved_composites = self.db.query(Composite).filter(
            Composite.material_id == material_id,
            Composite.status == CompositeStatus.APPROVED
        ).order_by(Composite.version.desc()).all()
        
        # Calculate 446 fields using field logic
        blue_line_data = await self.calculate_all_fields(
            material=material,
            material_type=material_type,
            composites=approved_composites,
            homologation_data=homologation_data
        )
        
        # Get default template
        default_template = self.db.query(QuestionnaireTemplate).filter(
            QuestionnaireTemplate.is_default == True,
            QuestionnaireTemplate.template_type == TemplateType.INITIAL_HOMOLOGATION
        ).first()
        
        # Convert blue_line_data to responses format (organized by fieldCode)
        responses = {}
        if default_template:
            # Map blue_line_data fields to fieldCode format
            for field in default_template.questions_schema:
                field_code = field.get("fieldCode", "")
                field_name = field.get("fieldName", "")
                # Try to find matching value in blue_line_data
                # This is a simplified mapping - you may need to adjust based on your field mapping logic
                if field_code and field_code in blue_line_data:
                    responses[field_code] = {
                        "value": blue_line_data[field_code],
                        "name": field_name,
                        "type": field.get("fieldType", "text")
                    }
                elif field_name and field_name in blue_line_data:
                    responses[field_code] = {
                        "value": blue_line_data[field_name],
                        "name": field_name,
                        "type": field.get("fieldType", "text")
                    }
        else:
            # Fallback: keep original format in blue_line_data
            responses = {}
        
        # Create or update Blue Line
        if existing_blue_line:
            existing_blue_line.blue_line_data = blue_line_data
            existing_blue_line.responses = responses if responses else existing_blue_line.responses
            existing_blue_line.template_id = default_template.id if default_template else existing_blue_line.template_id
            existing_blue_line.material_type = material_type
            existing_blue_line.calculated_at = datetime.now()
            existing_blue_line.calculation_metadata = {
                "last_calculation": datetime.now().isoformat(),
                "eligibility_details": eligibility_details,
                "composites_used": [c.id for c in approved_composites],
                "homologation_records_count": len(homologation_data) if homologation_data else 0
            }
            blue_line = existing_blue_line
            
            # Ensure composite exists for existing blue line
            if not blue_line.composite_id:
                composite = self._create_empty_composite(material_id)
                blue_line.composite_id = composite.id
                self.db.commit()
        else:
            # Create empty composite first
            composite = self._create_empty_composite(material_id)
            
            blue_line = BlueLine(
                material_id=material_id,
                template_id=default_template.id if default_template else None,
                responses=responses,
                blue_line_data=blue_line_data,  # Keep for backward compatibility
                material_type=material_type,
                composite_id=composite.id,
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
        
        logger.info(f"Blue Line calculated successfully for material {material_id}")
        return blue_line
    
    def _create_empty_composite(self, material_id: int) -> Composite:
        """Create an empty composite for a Blue Line"""
        # Get latest version for this material
        latest_composite = self.db.query(Composite).filter(
            Composite.material_id == material_id
        ).order_by(Composite.version.desc()).first()
        
        next_version = (latest_composite.version + 1) if latest_composite else 1
        
        composite = Composite(
            material_id=material_id,
            version=next_version,
            origin=CompositeOrigin.MANUAL,
            status=CompositeStatus.DRAFT,
            composite_metadata={},
            notes="Empty composite created for Blue Line - to be filled manually"
        )
        
        self.db.add(composite)
        self.db.commit()
        self.db.refresh(composite)
        
        logger.info(f"Created empty composite {composite.id} for Blue Line")
        return composite
    
    async def check_eligibility(
        self,
        material_id: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if material is eligible for Blue Line creation
        
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
        material_id: int
    ) -> List[Dict[str, Any]]:
        """
        Aggregate homologation records for all suppliers of this material, excluding CAN, REJ, EXP states
        
        Returns:
            List of valid homologation workflow data
        """
        excluded_states = [WorkflowStatus.CAN, WorkflowStatus.REJ, WorkflowStatus.EXP]
        
        workflows = self.db.query(ApprovalWorkflow).join(
            Composite, ApprovalWorkflow.composite_id == Composite.id
        ).filter(
            Composite.material_id == material_id,
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
        - {"source": "material.supplier_code"} -> Return material.supplier_code (if exists)
        - {"fixed_value": "LLUCH"} -> Return "LLUCH"
        - {"calculation": {"type": "count", "source": "composites"}} -> Return len(composites)
        
        Note: Blue Line is material-specific, not supplier-specific.
        If a field logic references supplier_code, it may return None or a default value.
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
                # Blue Line is material-specific, not supplier-specific
                # Return None or material's supplier_code if exists (for backward compatibility)
                return getattr(material, "supplier_code", None)
        
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
        material_id: int
    ) -> bool:
        """
        Handle case where all homologations for a material are rejected/cancelled/expired
        Should delete or empty the Blue Line
        
        Returns:
            True if Blue Line was deleted, False otherwise
        """
        # Check workflows for this material
        workflows = self.db.query(ApprovalWorkflow).join(
            Composite, ApprovalWorkflow.composite_id == Composite.id
        ).filter(
            Composite.material_id == material_id
        ).all()
        
        if workflows:
            all_rejected = all(
                workflow.status in [WorkflowStatus.CAN, WorkflowStatus.REJ, WorkflowStatus.EXP]
                for workflow in workflows
            )
            
            if all_rejected:
                # Delete Blue Line (one per material)
                blue_line = self.db.query(BlueLine).filter(
                    BlueLine.material_id == material_id
                ).first()
                
                if blue_line:
                    self.db.delete(blue_line)
                    self.db.commit()
                    logger.info(f"Deleted Blue Line for material {material_id} (all homologations rejected)")
                    return True
        
        return False

