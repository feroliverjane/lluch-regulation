from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import shutil
import logging

from app.core.database import get_db
from app.core.config import settings
from app.models.composite import Composite, CompositeStatus, CompositeType, CompositeComponent, CompositeOrigin
from app.models.approval_workflow import ApprovalWorkflow, WorkflowStatus
from app.schemas.composite import (
    CompositeCreate,
    CompositeResponse,
    CompositeCalculateRequest,
    CompositeCompareResponse
)
from app.services.composite_calculator import CompositeCalculator
from app.services.composite_comparator import CompositeComparator
from app.parsers.composite_excel_parser import CompositeExcelParser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/composites", tags=["composites"])


@router.post("/calculate", response_model=CompositeResponse, status_code=status.HTTP_201_CREATED)
def calculate_composite(
    request: CompositeCalculateRequest,
    db: Session = Depends(get_db)
):
    """Calculate a composite from chromatographic analyses"""
    calculator = CompositeCalculator(db)
    
    try:
        composite = calculator.calculate_from_lab_analyses(
            material_id=request.material_id,
            analysis_ids=request.analysis_ids,
            notes=request.notes
        )
        
        db.add(composite)
        db.commit()
        db.refresh(composite)
        
        return composite
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("", response_model=CompositeResponse, status_code=status.HTTP_201_CREATED)
def create_composite(
    composite_data: CompositeCreate,
    db: Session = Depends(get_db)
):
    """Create a composite manually"""
    calculator = CompositeCalculator(db)
    
    try:
        # Extract components from composite_data
        components_list = [comp.model_dump() for comp in composite_data.components]
        
        composite = calculator.calculate_from_documents(
            material_id=composite_data.material_id,
            components_data=components_list,
            notes=composite_data.notes
        )
        
        # Update origin and metadata
        composite.origin = composite_data.origin
        if composite_data.composite_metadata:
            composite.composite_metadata = composite_data.composite_metadata
        
        db.add(composite)
        db.commit()
        db.refresh(composite)
        
        return composite
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{composite_id}", response_model=CompositeResponse)
def get_composite(composite_id: int, db: Session = Depends(get_db)):
    """Get a specific composite"""
    composite = db.query(Composite).filter(Composite.id == composite_id).first()
    
    if not composite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Composite {composite_id} not found"
        )
    
    return composite


@router.get("/material/{material_id}", response_model=List[CompositeResponse])
def get_material_composites(
    material_id: int,
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[CompositeStatus] = None,
    db: Session = Depends(get_db)
):
    """Get all composites for a material"""
    query = db.query(Composite).filter(Composite.material_id == material_id)
    
    if status_filter:
        query = query.filter(Composite.status == status_filter)
    
    composites = query.order_by(Composite.version.desc()).offset(skip).limit(limit).all()
    
    return composites


@router.get("/{composite_id}/compare/{other_composite_id}", response_model=CompositeCompareResponse)
def compare_composites(
    composite_id: int,
    other_composite_id: int,
    db: Session = Depends(get_db)
):
    """Compare two composite versions"""
    comparator = CompositeComparator(db)
    
    try:
        comparison = comparator.compare_composites(composite_id, other_composite_id)
        return comparison
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/{composite_id}/submit-for-approval", response_model=CompositeResponse)
def submit_for_approval(
    composite_id: int,
    assigned_to_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Submit a composite for approval"""
    composite = db.query(Composite).filter(Composite.id == composite_id).first()
    
    if not composite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Composite {composite_id} not found"
        )
    
    if composite.status != CompositeStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only DRAFT composites can be submitted for approval"
        )
    
    # Update status
    composite.status = CompositeStatus.PENDING_APPROVAL
    
    # Create or update workflow
    workflow = db.query(ApprovalWorkflow).filter(
        ApprovalWorkflow.composite_id == composite_id
    ).first()
    
    if not workflow:
        workflow = ApprovalWorkflow(
            composite_id=composite_id,
            status=WorkflowStatus.PENDING,
            assigned_to_id=assigned_to_id
        )
        db.add(workflow)
    else:
        workflow.status = WorkflowStatus.PENDING
        workflow.assigned_to_id = assigned_to_id
    
    if assigned_to_id:
        workflow.assigned_at = datetime.now()
    
    db.commit()
    db.refresh(composite)
    
    return composite


@router.put("/{composite_id}/approve", response_model=CompositeResponse)
def approve_composite(
    composite_id: int,
    comments: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Approve a composite"""
    composite = db.query(Composite).filter(Composite.id == composite_id).first()
    
    if not composite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Composite {composite_id} not found"
        )
    
    if composite.status != CompositeStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PENDING_APPROVAL composites can be approved"
        )
    
    # Update composite
    composite.status = CompositeStatus.APPROVED
    composite.approved_at = datetime.now()
    
    # Update workflow
    workflow = db.query(ApprovalWorkflow).filter(
        ApprovalWorkflow.composite_id == composite_id
    ).first()
    
    if workflow:
        workflow.status = WorkflowStatus.APPROVED
        workflow.review_comments = comments
        workflow.reviewed_at = datetime.now()
        workflow.completed_at = datetime.now()
    
    db.commit()
    db.refresh(composite)
    
    return composite


@router.put("/{composite_id}/reject", response_model=CompositeResponse)
def reject_composite(
    composite_id: int,
    reason: str,
    comments: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Reject a composite"""
    composite = db.query(Composite).filter(Composite.id == composite_id).first()
    
    if not composite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Composite {composite_id} not found"
        )
    
    if composite.status != CompositeStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PENDING_APPROVAL composites can be rejected"
        )
    
    # Update composite
    composite.status = CompositeStatus.REJECTED
    
    # Update workflow
    workflow = db.query(ApprovalWorkflow).filter(
        ApprovalWorkflow.composite_id == composite_id
    ).first()
    
    if workflow:
        workflow.status = WorkflowStatus.REJECTED
        workflow.rejection_reason = reason
        workflow.review_comments = comments
        workflow.reviewed_at = datetime.now()
        workflow.completed_at = datetime.now()
    
    db.commit()
    db.refresh(composite)
    
    return composite


@router.delete("/{composite_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_composite(composite_id: int, db: Session = Depends(get_db)):
    """Delete a composite (only if DRAFT or REJECTED)"""
    composite = db.query(Composite).filter(Composite.id == composite_id).first()
    
    if not composite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Composite {composite_id} not found"
        )
    
    if composite.status not in [CompositeStatus.DRAFT, CompositeStatus.REJECTED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only DRAFT or REJECTED composites can be deleted"
        )
    
    db.delete(composite)
    db.commit()
    
    return None


# ===== NEW COMPOSITE COMPARISON AND AVERAGING =====

@router.post("/average", response_model=CompositeResponse)
def create_average_composite(
    composite_a_id: int,
    composite_b_id: int,
    target_material_id: int,
    db: Session = Depends(get_db)
):
    """
    Create average composite from two composites.
    Used for Z1 composite updates.
    """
    from app.services.composite_comparison_service import CompositeComparisonService
    
    comparison_service = CompositeComparisonService(db)
    
    try:
        averaged_composite = comparison_service.calculate_average_composite(
            composite_a_id,
            composite_b_id,
            target_material_id
        )
        
        db.add(averaged_composite)
        db.commit()
        db.refresh(averaged_composite)
        
        return averaged_composite
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating average composite: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating average composite: {str(e)}"
        )


@router.post("/compare-detailed", response_model=dict)
def compare_composites_detailed(
    composite_a_id: int,
    composite_b_id: int,
    db: Session = Depends(get_db)
):
    """
    Compare two composites in detail.
    Returns components added, removed, changed with match score.
    """
    from app.services.composite_comparison_service import CompositeComparisonService
    
    comparison_service = CompositeComparisonService(db)
    
    try:
        comparison_result = comparison_service.compare_composites(
            composite_a_id,
            composite_b_id
        )
        
        return comparison_result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{composite_id}/import-z2-from-excel", response_model=CompositeResponse)
async def import_z2_from_excel(
    composite_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Import composite Z2 from Excel/CSV file (SAP format).
    Updates an existing Z1 composite to Z2 with data from the Excel file.
    
    The Excel/CSV should have columns:
    - Espec./compon. or CAS: CAS number
    - Nombre del producto: Component name
    - Cl.Componente: Must be 'COMPONENT' for main components
    - Valor Lím.inf. and Valor Lím.sup.: Percentage range
    - Unidad: Unit (usually '%')
    """
    composite = db.query(Composite).filter(Composite.id == composite_id).first()
    
    if not composite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Composite {composite_id} not found"
        )
    
    # Log current composite state for debugging
    logger.info(f"🔍 Composite actual: ID={composite.id}, Tipo={composite.composite_type}, Componentes={len(composite.components)}")
    
    # Validate file type
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ['.xlsx', '.xls', '.csv']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato de archivo no soportado: {file_ext}. Use .xlsx, .xls o .csv"
        )
    
    # Save file temporarily
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"composite_z2_{timestamp}_{file.filename}"
    file_path = upload_dir / filename
    
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Parse Excel/CSV
        parser = CompositeExcelParser()
        parse_result = parser.parse_file(str(file_path))
        
        if not parse_result["success"]:
            errors = parse_result.get("errors", [])
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Error parseando archivo: {'; '.join(errors)}"
            )
        
        components_data = parse_result["components"]
        
        if not components_data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No se encontraron componentes en el archivo"
            )
        
        logger.info(f"Importando {len(components_data)} componentes desde Excel para composite {composite_id}")
        
        # Save Z1 state before updating (for comparison)
        z1_composite = None
        z1_components_snapshot = None
        
        # Check if composite is Z1 - treat None as Z1 (new composites might not have type set)
        # Only skip comparison if it's explicitly Z2
        is_z1 = composite.composite_type != CompositeType.Z2
        
        logger.info(f"🔍 Verificando tipo de composite: tipo={composite.composite_type}, is_z1={is_z1}, tiene_componentes={len(composite.components) > 0}")
        
        if is_z1 and composite.components:
            # Create a snapshot of Z1 components before deletion
            z1_components_snapshot = [
                {
                    "cas_number": c.cas_number,
                    "component_name": c.component_name,
                    "percentage": c.percentage,
                    "component_type": c.component_type.value if c.component_type else "COMPONENT"
                }
                for c in composite.components
            ]
            z1_composite = composite  # Reference to original composite
            logger.info(f"✅ Snapshot de Z1 capturado: {len(z1_components_snapshot)} componentes para comparación")
        else:
            if composite.composite_type == CompositeType.Z2:
                logger.warning(f"⚠️  Composite ya es Z2 (tipo: {composite.composite_type}), no se puede generar comparación")
            elif not composite.components:
                logger.warning(f"⚠️  Composite no tiene componentes, no se generará comparación")
            else:
                logger.warning(f"⚠️  Composite no es Z1 (tipo: {composite.composite_type}), no se generará comparación")
        
        # Delete existing components
        for comp in composite.components:
            db.delete(comp)
        
        # Add new components from Excel
        for comp_data in components_data:
            component = CompositeComponent(
                composite_id=composite_id,
                cas_number=comp_data.get("cas_number"),
                component_name=comp_data["component_name"],
                percentage=comp_data["percentage"],
                component_type=comp_data.get("component_type", "COMPONENT"),
                notes=f"Importado desde Excel: {comp_data.get('percentage_min', 0)}-{comp_data.get('percentage_max', 0)}%"
            )
            composite.components.append(component)
        
        # Update composite to Z2
        composite.composite_type = CompositeType.Z2
        composite.origin = CompositeOrigin.MANUAL  # Z2 imported manually
        
        # Update metadata
        existing_metadata = composite.composite_metadata or {}
        existing_metadata.update({
            "import_source": "excel",
            "import_filename": file.filename,
            "import_date": datetime.utcnow().isoformat(),
            "total_percentage": parse_result.get("total_percentage", 0),
            "z1_snapshot": z1_components_snapshot if z1_composite else None
        })
        composite.composite_metadata = existing_metadata
        composite.notes = f"Composite Z2 importado desde {file.filename} con {len(components_data)} componentes"
        
        db.commit()
        db.refresh(composite)
        
        logger.info(f"Composite {composite_id} actualizado a Z2 con {len(components_data)} componentes")
        
        # Perform comparison if we had a Z1 composite
        comparison_result = None
        ai_analysis = None
        
        logger.info(f"🔍 Verificando comparación: z1_composite={z1_composite is not None}, snapshot={z1_components_snapshot is not None}")
        
        if z1_composite and z1_components_snapshot:
            logger.info(f"✅ Iniciando comparación Z1 → Z2 con {len(z1_components_snapshot)} componentes Z1 y {len(composite.components)} componentes Z2")
            try:
                # Create temporary Z1 composite for comparison
                from app.services.composite_comparison_service import CompositeComparisonService
                from app.services.composite_ai_analyzer import CompositeAIAnalyzer
                
                comparison_service = CompositeComparisonService(db)
                
                # Create a temporary composite object with Z1 data for comparison
                # We'll compare using the snapshot data
                # Use CAS number as primary key, but fallback to component_name if CAS is None
                z1_temp_components = {}
                for c in z1_components_snapshot:
                    key = c.get("cas_number") or c.get("component_name", "").upper()
                    z1_temp_components[key] = c
                
                z2_components = {}
                for c in composite.components:
                    key = c.cas_number or c.component_name.upper()
                    z2_components[key] = c
                
                # Build comparison manually since we can't query Z1 anymore
                added = []
                removed = []
                changed = []
                
                # Check for new components in Z2
                for cas, comp_z2 in z2_components.items():
                    if cas not in z1_temp_components:
                        added.append({
                            "component_name": comp_z2.component_name,
                            "cas_number": cas,
                            "old_percentage": None,
                            "new_percentage": comp_z2.percentage,
                            "change": comp_z2.percentage,
                            "change_percent": None
                        })
                
                # Check for removed components
                for cas, comp_z1 in z1_temp_components.items():
                    if cas not in z2_components:
                        removed.append({
                            "component_name": comp_z1["component_name"],
                            "cas_number": cas,
                            "old_percentage": comp_z1["percentage"],
                            "new_percentage": None,
                            "change": -comp_z1["percentage"],
                            "change_percent": None
                        })
                
                # Check for changed components
                for cas, comp_z1 in z1_temp_components.items():
                    if cas in z2_components:
                        comp_z2 = z2_components[cas]
                        change = comp_z2.percentage - comp_z1["percentage"]
                        change_percent = (change / comp_z1["percentage"] * 100) if comp_z1["percentage"] > 0 else 0
                        
                        if abs(change) > 0.01:
                            changed.append({
                                "component_name": comp_z1["component_name"],
                                "cas_number": cas,
                                "old_percentage": comp_z1["percentage"],
                                "new_percentage": comp_z2.percentage,
                                "change": change,
                                "change_percent": change_percent
                            })
                
                # Calculate match score
                total_change_score = sum(abs(c["change"]) for c in changed)
                total_change_score += sum(c["change"] for c in added)
                total_change_score += sum(abs(c["change"]) for c in removed)
                match_score = max(0, 100 - total_change_score)
                
                comparison_result = {
                    "z1_composite_id": composite_id,  # Same ID, but was Z1
                    "z2_composite_id": composite_id,
                    "components_added": added,
                    "components_removed": removed,
                    "components_changed": changed,
                    "total_change_score": total_change_score,
                    "match_score": match_score,
                    "significant_changes": any(abs(c.get("change", 0)) >= 5.0 for c in changed)
                }
                logger.info(f"✅ Comparación generada: {len(added)} agregados, {len(removed)} eliminados, {len(changed)} modificados, match_score={match_score:.1f}%")
                
                # Perform AI analysis
                try:
                    ai_analyzer = CompositeAIAnalyzer(db)
                    # Create temporary composite objects for AI analysis
                    z1_for_ai = type('obj', (object,), {
                        'components': [
                            type('comp', (object,), {
                                'component_name': c["component_name"],
                                'cas_number': c["cas_number"],
                                'percentage': c["percentage"]
                            })() for c in z1_components_snapshot
                        ]
                    })()
                    
                    ai_analysis = ai_analyzer.analyze_z1_to_z2_changes(
                        z1_for_ai,
                        composite,
                        comparison_result
                    )
                except Exception as e:
                    logger.warning(f"AI analysis failed: {e}", exc_info=True)
                    ai_analysis = {
                        "ai_analysis_available": False,
                        "error": str(e)
                    }
                
            except Exception as e:
                logger.warning(f"Comparison failed: {e}", exc_info=True)
                comparison_result = {
                    "error": str(e),
                    "message": "Could not perform comparison"
                }
        
        # Return composite with comparison data
        response_data = {
            "composite": composite,
            "comparison": comparison_result,
            "ai_analysis": ai_analysis
        }
        
        # Return as dict since we're adding extra fields
        from fastapi.responses import JSONResponse
        return JSONResponse(content={
            "id": composite.id,
            "material_id": composite.material_id,
            "version": composite.version,
            "composite_type": composite.composite_type.value,
            "status": composite.status.value,
            "origin": composite.origin.value,
            "components": [
                {
                    "id": c.id,
                    "cas_number": c.cas_number,
                    "component_name": c.component_name,
                    "percentage": c.percentage,
                    "component_type": c.component_type.value if c.component_type else "COMPONENT"
                }
                for c in composite.components
            ],
            "comparison": comparison_result,
            "ai_analysis": ai_analysis
        })
        
        logger.info(f"📤 Retornando respuesta: comparison={comparison_result is not None}, ai_analysis={ai_analysis is not None}")
        if comparison_result:
            logger.info(f"   - Comparación: {len(comparison_result.get('components_added', []))} agregados, "
                       f"{len(comparison_result.get('components_removed', []))} eliminados, "
                       f"{len(comparison_result.get('components_changed', []))} modificados")
        else:
            logger.warning(f"   ⚠️  No se generó comparación. z1_composite={z1_composite is not None}, snapshot={z1_components_snapshot is not None}")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error importando Z2 desde Excel: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error importando composite Z2: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                logger.warning(f"No se pudo eliminar archivo temporal {file_path}: {e}")

