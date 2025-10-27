from celery import shared_task
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from app.core.database import SessionLocal
from app.models.material import Material
from app.models.approval_workflow import ApprovalWorkflow, WorkflowStatus
from app.models.composite import Composite
from app.models.blue_line import BlueLine, BlueLineSyncStatus
from app.services.blue_line_calculator import BlueLineCalculator
from app.services.blue_line_sync_service import BlueLineSyncService
from app.core.config import settings

logger = logging.getLogger(__name__)


@shared_task(name="blue_line.auto_generate_on_approval")
def auto_generate_blue_line_on_approval(workflow_id: int):
    """
    Triggered when approval workflow reaches APC/APR state
    Automatically generates or updates Blue Line
    
    Args:
        workflow_id: ApprovalWorkflow ID that triggered the generation
    """
    db = SessionLocal()
    try:
        logger.info(f"Auto-generating Blue Line for workflow {workflow_id}")
        
        # Get workflow and composite
        workflow = db.query(ApprovalWorkflow).filter(
            ApprovalWorkflow.id == workflow_id
        ).first()
        
        if not workflow:
            logger.error(f"Workflow {workflow_id} not found")
            return
        
        # Check if regulatory status is APC or APR
        is_approved = (
            workflow.regulatory_status in ["APC", "APR"] or
            workflow.status in [WorkflowStatus.APC, WorkflowStatus.APR]
        )
        
        if not is_approved:
            logger.info(f"Workflow {workflow_id} not in APC/APR state, skipping Blue Line generation")
            return
        
        # Get composite and material
        composite = db.query(Composite).filter(
            Composite.id == workflow.composite_id
        ).first()
        
        if not composite:
            logger.error(f"Composite {workflow.composite_id} not found")
            return
        
        material = db.query(Material).filter(
            Material.id == composite.material_id
        ).first()
        
        if not material or not material.supplier_code:
            logger.error(f"Material {composite.material_id} not found or missing supplier_code")
            return
        
        # Calculate Blue Line
        calculator = BlueLineCalculator(db)
        
        # Use asyncio.run for async function
        import asyncio
        blue_line = asyncio.run(calculator.calculate_blue_line(
            material_id=material.id,
            supplier_code=material.supplier_code,
            force_recalculate=True
        ))
        
        if blue_line:
            logger.info(f"Successfully generated Blue Line {blue_line.id} for material {material.id}")
        else:
            logger.warning(f"Blue Line not generated for material {material.id} (not eligible)")
        
    except Exception as e:
        logger.error(f"Error auto-generating Blue Line for workflow {workflow_id}: {e}")
    finally:
        db.close()


@shared_task(name="blue_line.check_purchase_history")
def check_and_update_purchase_history():
    """
    Daily task to check ERP for purchase history and update material eligibility
    """
    db = SessionLocal()
    try:
        logger.info("Starting daily purchase history check")
        
        # Get all materials with supplier codes
        materials = db.query(Material).filter(
            Material.is_active == True,
            Material.supplier_code.isnot(None)
        ).all()
        
        from app.integrations.erp_adapter import ERPAdapter
        erp_adapter = ERPAdapter()
        
        updated_count = 0
        
        for material in materials:
            try:
                # Get purchase history from ERP
                import asyncio
                purchase_history = asyncio.run(
                    erp_adapter.get_purchase_history_last_n_years(
                        material.reference_code,
                        settings.BLUE_LINE_PURCHASE_LOOKBACK_YEARS
                    )
                )
                
                if purchase_history:
                    # Update last purchase date if purchases found
                    if purchase_history and len(purchase_history) > 0:
                        # Get most recent purchase
                        latest_purchase = max(
                            purchase_history,
                            key=lambda x: x.get('purchase_date', '1900-01-01')
                        )
                        purchase_date_str = latest_purchase.get('purchase_date')
                        
                        if purchase_date_str:
                            material.last_purchase_date = datetime.fromisoformat(purchase_date_str)
                            updated_count += 1
            
            except Exception as e:
                logger.error(f"Error checking purchase history for material {material.id}: {e}")
                continue
        
        db.commit()
        logger.info(f"Purchase history check completed. Updated {updated_count} materials")
        
    except Exception as e:
        logger.error(f"Error in purchase history check task: {e}")
    finally:
        db.close()


@shared_task(name="blue_line.periodic_sync")
def periodic_blue_line_sync():
    """
    Hourly task to sync pending Blue Lines to SAP
    """
    db = SessionLocal()
    try:
        logger.info("Starting periodic Blue Line sync")
        
        sync_service = BlueLineSyncService(db)
        
        # Run bulk sync
        import asyncio
        results = asyncio.run(sync_service.bulk_sync_pending())
        
        logger.info(f"Periodic sync completed: {results['success']} success, {results['failed']} failed")
        
    except Exception as e:
        logger.error(f"Error in periodic Blue Line sync: {e}")
    finally:
        db.close()


@shared_task(name="blue_line.recalculate_on_status_change")
def recalculate_blue_lines_on_status_change(workflow_id: int):
    """
    Triggered when approval status changes to CAN, REJ, or EXP
    Recalculates or deletes Blue Line if needed
    
    Args:
        workflow_id: ApprovalWorkflow ID that changed status
    """
    db = SessionLocal()
    try:
        logger.info(f"Recalculating Blue Line for workflow {workflow_id} status change")
        
        # Get workflow
        workflow = db.query(ApprovalWorkflow).filter(
            ApprovalWorkflow.id == workflow_id
        ).first()
        
        if not workflow:
            logger.error(f"Workflow {workflow_id} not found")
            return
        
        # Check if status is exclusion state
        exclusion_states = [WorkflowStatus.CAN, WorkflowStatus.REJ, WorkflowStatus.EXP]
        
        if workflow.status not in exclusion_states:
            logger.info(f"Workflow {workflow_id} not in exclusion state, skipping")
            return
        
        # Get composite and material
        composite = db.query(Composite).filter(
            Composite.id == workflow.composite_id
        ).first()
        
        if not composite:
            return
        
        material = db.query(Material).filter(
            Material.id == composite.material_id
        ).first()
        
        if not material or not material.supplier_code:
            return
        
        # Check if single provider rejection
        calculator = BlueLineCalculator(db)
        
        import asyncio
        was_deleted = asyncio.run(calculator.handle_single_provider_rejection(
            material.id,
            material.supplier_code
        ))
        
        if was_deleted:
            logger.info(f"Deleted Blue Line for material {material.id} (single provider rejection)")
        else:
            # Recalculate Blue Line (will exclude this workflow)
            blue_line = asyncio.run(calculator.calculate_blue_line(
                material_id=material.id,
                supplier_code=material.supplier_code,
                force_recalculate=True
            ))
            
            if blue_line:
                logger.info(f"Recalculated Blue Line {blue_line.id} after status change")
        
    except Exception as e:
        logger.error(f"Error recalculating Blue Line for workflow {workflow_id}: {e}")
    finally:
        db.close()


@shared_task(name="blue_line.initial_generation")
def initial_blue_line_generation(batch_size: int = 50):
    """
    One-time bulk generation of Blue Lines for all eligible materials
    Useful for initial system setup (ZMM110 data migration)
    
    Args:
        batch_size: Number of materials to process in each batch
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting initial Blue Line generation (batch size: {batch_size})")
        
        # Get all active materials with supplier codes that don't have Blue Lines
        materials_query = db.query(Material).filter(
            Material.is_active == True,
            Material.supplier_code.isnot(None),
            ~Material.id.in_(
                db.query(BlueLine.material_id).distinct()
            )
        ).limit(batch_size)
        
        materials = materials_query.all()
        
        calculator = BlueLineCalculator(db)
        
        generated = 0
        skipped = 0
        errors = 0
        
        for material in materials:
            try:
                import asyncio
                blue_line = asyncio.run(calculator.calculate_blue_line(
                    material_id=material.id,
                    supplier_code=material.supplier_code,
                    force_recalculate=False
                ))
                
                if blue_line:
                    generated += 1
                else:
                    skipped += 1
            
            except Exception as e:
                logger.error(f"Error generating Blue Line for material {material.id}: {e}")
                errors += 1
        
        logger.info(f"Initial generation batch completed: {generated} generated, {skipped} skipped, {errors} errors")
        
        # If there are more materials, schedule another batch
        remaining = db.query(Material).filter(
            Material.is_active == True,
            Material.supplier_code.isnot(None),
            ~Material.id.in_(
                db.query(BlueLine.material_id).distinct()
            )
        ).count()
        
        if remaining > 0:
            logger.info(f"{remaining} materials remaining, scheduling next batch")
            # Schedule next batch (would use Celery task chaining in production)
            initial_blue_line_generation.apply_async(
                args=[batch_size],
                countdown=60  # Wait 60 seconds before next batch
            )
        
    except Exception as e:
        logger.error(f"Error in initial Blue Line generation: {e}")
    finally:
        db.close()


@shared_task(name="blue_line.sync_z2_materials_from_sap")
def sync_z2_materials_from_sap():
    """
    Daily task to import composite data from SAP for Z2 materials
    """
    db = SessionLocal()
    try:
        logger.info("Starting Z2 materials import from SAP")
        
        # Get all Z2 materials
        z2_materials = db.query(Material).filter(
            Material.is_active == True,
            Material.sap_status == "Z2"
        ).all()
        
        sync_service = BlueLineSyncService(db)
        
        success_count = 0
        failed_count = 0
        
        for material in z2_materials:
            try:
                import asyncio
                result = asyncio.run(sync_service.import_from_sap(material.id))
                
                if result['success']:
                    success_count += 1
                else:
                    failed_count += 1
            
            except Exception as e:
                logger.error(f"Error importing SAP data for material {material.id}: {e}")
                failed_count += 1
        
        logger.info(f"Z2 SAP import completed: {success_count} success, {failed_count} failed")
        
    except Exception as e:
        logger.error(f"Error in Z2 SAP import task: {e}")
    finally:
        db.close()

