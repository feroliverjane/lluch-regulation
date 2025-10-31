from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import shutil
import logging

from app.core.database import get_db
from app.models.blue_line import BlueLine
from app.models.blue_line_field_logic import BlueLineFieldLogic
from app.models.material import Material
from app.schemas.blue_line import (
    BlueLineResponse,
    BlueLineCalculateRequest,
    BlueLineSyncRequest,
    BlueLineSyncResponse,
    BlueLineEligibilityCheck,
    BlueLineFieldLogicCreate,
    BlueLineFieldLogicUpdate,
    BlueLineFieldLogicResponse,
    BlueLineFieldLogicBulkImport,
)
from app.services.blue_line_calculator import BlueLineCalculator
from app.services.blue_line_sync_service import BlueLineSyncService
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/blue-line", tags=["blue-line"])


@router.post("/calculate", response_model=BlueLineResponse, status_code=status.HTTP_201_CREATED)
async def calculate_blue_line(
    request: BlueLineCalculateRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate Blue Line for a material
    
    This endpoint:
    1. Checks eligibility (purchase history, approval states)
    2. Calculates all 446 fields based on configured logic
    3. Creates or updates the Blue Line record (one per material)
    """
    calculator = BlueLineCalculator(db)
    
    try:
        blue_line = await calculator.calculate_blue_line(
            material_id=request.material_id,
            force_recalculate=request.force_recalculate
        )
        
        if not blue_line:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Material is not eligible for Blue Line or calculation failed"
            )
        
        return blue_line
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/material/{material_id}", response_model=BlueLineResponse)
def get_blue_line_by_material(
    material_id: int,
    db: Session = Depends(get_db)
):
    """Get Blue Line for a material (one Blue Line per material)"""
    blue_line = db.query(BlueLine).filter(
        BlueLine.material_id == material_id
    ).first()
    
    if not blue_line:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blue Line not found for material {material_id}"
        )
    
    return blue_line


@router.get("/{blue_line_id}", response_model=BlueLineResponse)
def get_blue_line(
    blue_line_id: int,
    db: Session = Depends(get_db)
):
    """Get Blue Line by ID"""
    blue_line = db.query(BlueLine).filter(BlueLine.id == blue_line_id).first()
    
    if not blue_line:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blue Line {blue_line_id} not found"
        )
    
    return blue_line


@router.get("", response_model=List[BlueLineResponse])
def list_blue_lines(
    skip: int = 0,
    limit: int = 100,
    material_type: Optional[str] = None,
    sync_status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all Blue Lines with optional filters"""
    query = db.query(BlueLine)
    
    if material_type:
        query = query.filter(BlueLine.material_type == material_type)
    
    if sync_status:
        query = query.filter(BlueLine.sync_status == sync_status)
    
    blue_lines = query.offset(skip).limit(limit).all()
    return blue_lines


@router.post("/{blue_line_id}/sync-to-sap", response_model=BlueLineSyncResponse)
async def sync_blue_line_to_sap(
    blue_line_id: int,
    db: Session = Depends(get_db)
):
    """
    Manually trigger sync of Blue Line to SAP Composite (Z1 materials)
    """
    sync_service = BlueLineSyncService(db)
    
    result = await sync_service.sync_to_sap(blue_line_id)
    
    return BlueLineSyncResponse(**result)


@router.post("/material/{material_id}/import-from-sap", response_model=BlueLineSyncResponse)
async def import_blue_line_from_sap(
    material_id: int,
    db: Session = Depends(get_db)
):
    """
    Manually trigger import from SAP Composite to Blue Line (Z2 materials)
    """
    sync_service = BlueLineSyncService(db)
    
    result = await sync_service.import_from_sap(material_id)
    
    return BlueLineSyncResponse(**result)


@router.get("/eligible-materials/list", response_model=List[BlueLineEligibilityCheck])
async def list_eligible_materials(
    db: Session = Depends(get_db)
):
    """
    List all materials eligible for Blue Line creation
    Checks: purchase history, approval states
    
    Note: Blue Line is associated with a material, not a supplier.
    When questionnaires arrive from different suppliers, they are all
    compared against the same Blue Line for that material.
    """
    calculator = BlueLineCalculator(db)
    
    # Get all active materials
    materials = db.query(Material).filter(
        Material.is_active == True
    ).all()
    
    eligibility_results = []
    
    for material in materials:
        is_eligible, details = await calculator.check_eligibility(material.id)
        
        eligibility_results.append(
            BlueLineEligibilityCheck(
                material_id=material.id,
                is_eligible=is_eligible,
                reasons=details.get("reasons", []),
                has_purchase_history=details.get("has_purchase_history", False),
                regulatory_status_ok=details.get("regulatory_status_ok", False),
                technical_status_ok=details.get("technical_status_ok", False),
                purchase_date=material.last_purchase_date
            )
        )
    
    return eligibility_results


@router.get("/check-eligibility/material/{material_id}", response_model=BlueLineEligibilityCheck)
async def check_eligibility(
    material_id: int,
    db: Session = Depends(get_db)
):
    """
    Check if a specific material is eligible for Blue Line
    
    The Blue Line is associated with a material (not a supplier).
    When a questionnaire arrives from any supplier, it is compared against 
    the Blue Line for that material.
    """
    calculator = BlueLineCalculator(db)
    
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Material {material_id} not found"
        )
    
    is_eligible, details = await calculator.check_eligibility(material_id)
    
    return BlueLineEligibilityCheck(
        material_id=material_id,
        is_eligible=is_eligible,
        reasons=details.get("reasons", []),
        has_purchase_history=details.get("has_purchase_history", False),
        regulatory_status_ok=details.get("regulatory_status_ok", False),
        technical_status_ok=details.get("technical_status_ok", False),
        purchase_date=material.last_purchase_date
    )


@router.delete("/{blue_line_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_blue_line(
    blue_line_id: int,
    db: Session = Depends(get_db)
):
    """Delete a Blue Line record"""
    blue_line = db.query(BlueLine).filter(BlueLine.id == blue_line_id).first()
    
    if not blue_line:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blue Line {blue_line_id} not found"
        )
    
    db.delete(blue_line)
    db.commit()


# Field Logic Management Endpoints

@router.post("/field-logic", response_model=BlueLineFieldLogicResponse, status_code=status.HTTP_201_CREATED)
def create_field_logic(
    field_logic: BlueLineFieldLogicCreate,
    db: Session = Depends(get_db)
):
    """Create a new field logic configuration"""
    # Check if field already exists
    existing = db.query(BlueLineFieldLogic).filter(
        BlueLineFieldLogic.field_name == field_logic.field_name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Field logic for '{field_logic.field_name}' already exists"
        )
    
    db_field_logic = BlueLineFieldLogic(**field_logic.model_dump())
    db.add(db_field_logic)
    db.commit()
    db.refresh(db_field_logic)
    
    return db_field_logic


@router.get("/field-logic", response_model=List[BlueLineFieldLogicResponse])
def list_field_logics(
    skip: int = 0,
    limit: int = 500,
    is_active: Optional[bool] = None,
    material_type_filter: Optional[str] = None,
    field_category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all field logic configurations"""
    query = db.query(BlueLineFieldLogic)
    
    if is_active is not None:
        query = query.filter(BlueLineFieldLogic.is_active == is_active)
    
    if material_type_filter:
        query = query.filter(BlueLineFieldLogic.material_type_filter == material_type_filter)
    
    if field_category:
        query = query.filter(BlueLineFieldLogic.field_category == field_category)
    
    field_logics = query.order_by(BlueLineFieldLogic.priority).offset(skip).limit(limit).all()
    return field_logics


@router.get("/field-logic/{field_logic_id}", response_model=BlueLineFieldLogicResponse)
def get_field_logic(
    field_logic_id: int,
    db: Session = Depends(get_db)
):
    """Get field logic by ID"""
    field_logic = db.query(BlueLineFieldLogic).filter(
        BlueLineFieldLogic.id == field_logic_id
    ).first()
    
    if not field_logic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Field logic {field_logic_id} not found"
        )
    
    return field_logic


@router.put("/field-logic/{field_logic_id}", response_model=BlueLineFieldLogicResponse)
def update_field_logic(
    field_logic_id: int,
    field_logic_update: BlueLineFieldLogicUpdate,
    db: Session = Depends(get_db)
):
    """Update field logic configuration"""
    field_logic = db.query(BlueLineFieldLogic).filter(
        BlueLineFieldLogic.id == field_logic_id
    ).first()
    
    if not field_logic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Field logic {field_logic_id} not found"
        )
    
    # Update fields
    update_data = field_logic_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(field_logic, field, value)
    
    db.commit()
    db.refresh(field_logic)
    
    return field_logic


@router.delete("/field-logic/{field_logic_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_field_logic(
    field_logic_id: int,
    db: Session = Depends(get_db)
):
    """Delete field logic configuration"""
    field_logic = db.query(BlueLineFieldLogic).filter(
        BlueLineFieldLogic.id == field_logic_id
    ).first()
    
    if not field_logic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Field logic {field_logic_id} not found"
        )
    
    db.delete(field_logic)
    db.commit()


@router.post("/field-logic/bulk-import", response_model=dict)
def bulk_import_field_logics(
    bulk_import: BlueLineFieldLogicBulkImport,
    db: Session = Depends(get_db)
):
    """
    Bulk import field logic configurations
    Useful for initial setup of the 446 fields
    """
    created = 0
    updated = 0
    errors = []
    
    for field_logic_data in bulk_import.field_logics:
        try:
            existing = db.query(BlueLineFieldLogic).filter(
                BlueLineFieldLogic.field_name == field_logic_data.field_name
            ).first()
            
            if existing:
                if bulk_import.overwrite_existing:
                    # Update existing
                    for field, value in field_logic_data.model_dump().items():
                        setattr(existing, field, value)
                    updated += 1
                else:
                    # Skip
                    continue
            else:
                # Create new
                new_field_logic = BlueLineFieldLogic(**field_logic_data.model_dump())
                db.add(new_field_logic)
                created += 1
        
        except Exception as e:
            errors.append({
                "field_name": field_logic_data.field_name,
                "error": str(e)
            })
    
    db.commit()
    
    return {
        "success": True,
        "created": created,
        "updated": updated,
        "errors": errors,
        "total_processed": len(bulk_import.field_logics)
    }

@router.post("/{blue_line_id}/upload-documents", response_model=dict)
async def upload_documents_for_composite(
    blue_line_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload PDF documents for composite extraction from Blue Line.
    Stores documents temporarily for AI extraction.
    """
    from pathlib import Path
    import shutil
    from datetime import datetime
    
    blue_line = db.query(BlueLine).filter(BlueLine.id == blue_line_id).first()
    if not blue_line:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blue Line {blue_line_id} not found"
        )
    
    # Create upload directory for blue line documents
    upload_dir = Path(settings.UPLOAD_DIR) / "blue-lines" / str(blue_line_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    uploaded_files = []
    
    for file in files:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only PDF files are supported, got {file.filename}"
            )
        
        # Save file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = upload_dir / safe_filename
        
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        uploaded_files.append({
            "filename": file.filename,
            "path": str(file_path.resolve()),
            "upload_date": datetime.utcnow().isoformat(),
            "type": "pdf"
        })
    
    # Store documents in blue line metadata temporarily
    # Create a new dict to ensure SQLAlchemy detects the change
    current_metadata = blue_line.calculation_metadata.copy() if blue_line.calculation_metadata else {}
    
    if "pending_documents" not in current_metadata:
        current_metadata["pending_documents"] = []
    
    # Extend the list
    current_metadata["pending_documents"].extend(uploaded_files)
    
    # Assign the new dict to trigger SQLAlchemy change detection
    blue_line.calculation_metadata = current_metadata
    
    db.add(blue_line)  # Ensure the object is tracked
    db.commit()
    db.refresh(blue_line)  # Refresh to get the latest data
    
    # Verify the documents were saved
    final_pending_docs = blue_line.calculation_metadata.get("pending_documents", []) if blue_line.calculation_metadata else []
    
    logger.info(f"Uploaded {len(uploaded_files)} file(s) for Blue Line {blue_line_id}")
    logger.info(f"Total pending documents after save: {len(final_pending_docs)}")
    
    return {
        "blue_line_id": blue_line_id,
        "uploaded_files": uploaded_files,
        "total_documents": len(final_pending_docs)
    }


@router.post("/{blue_line_id}/extract-composite", response_model=dict, status_code=status.HTTP_201_CREATED)
async def extract_composite_from_blue_line(
    blue_line_id: int,
    db: Session = Depends(get_db)
):
    """
    Extract composite Z1 from uploaded documents using AI.
    Uses the same AI extraction logic as questionnaires.
    """
    from pathlib import Path
    from app.models.composite import Composite, CompositeComponent, CompositeOrigin, CompositeStatus, CompositeType
    from app.core.config import settings
    
    blue_line = db.query(BlueLine).filter(BlueLine.id == blue_line_id).first()
    if not blue_line:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blue Line {blue_line_id} not found"
        )
    
    # Get pending documents from metadata
    pending_docs = blue_line.calculation_metadata.get("pending_documents", []) if blue_line.calculation_metadata else []
    
    if not pending_docs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No documents uploaded. Please upload PDF documents first using /upload-documents endpoint."
        )
    
    # Extract PDF paths and validate they exist
    pdf_paths = []
    missing_files = []
    
    for doc in pending_docs:
        if doc.get("type") == "pdf":
            doc_path = Path(doc["path"])
            if doc_path.exists():
                pdf_paths.append(str(doc_path.resolve()))
            else:
                missing_files.append(doc["path"])
                logger.warning(f"PDF file not found: {doc_path}")
    
    if not pdf_paths:
        error_msg = "No PDF documents found"
        if missing_files:
            error_msg += f". Missing files: {', '.join(missing_files)}"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    logger.info(f"Extracting composite from {len(pdf_paths)} PDF(s) for Blue Line {blue_line_id}")
    
    # Extract composite - Use OpenAI if configured, otherwise use OCR
    try:
        if settings.USE_OPENAI_FOR_EXTRACTION and settings.OPENAI_API_KEY:
            # Use OpenAI Vision API (more accurate)
            from app.services.composite_extractor_openai import CompositeExtractorOpenAI
            extractor = CompositeExtractorOpenAI(api_key=settings.OPENAI_API_KEY)
            components, confidence = extractor.extract_from_pdfs(pdf_paths, use_vision=True)
            extraction_method = "OPENAI_VISION"
        else:
            # Use OCR-based extraction (local, no API needed)
            from app.services.composite_extractor_ai import CompositeExtractorAI
            extractor = CompositeExtractorAI()
            components, confidence = extractor.extract_from_pdfs(pdf_paths)
            extraction_method = "AI_OCR"
        
        if not components:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No components could be extracted from documents"
            )
        
        # Check if composite already exists
        existing_composite = None
        if blue_line.composite_id:
            existing_composite = db.query(Composite).filter(Composite.id == blue_line.composite_id).first()
        
        # Create or update composite
        if existing_composite and not existing_composite.components:
            # Update existing empty composite
            composite = existing_composite
            composite.composite_type = CompositeType.Z1
            composite.origin = CompositeOrigin.CALCULATED
            composite.status = CompositeStatus.DRAFT
            composite.source_documents = pending_docs
            composite.extraction_confidence = confidence
            composite.composite_metadata = {
                "extraction_method": extraction_method,
                "extraction_date": datetime.utcnow().isoformat(),
                "source_blue_line": blue_line_id
            }
            composite.notes = f"Extracted from {len(pdf_paths)} document(s) with {confidence:.1f}% confidence"
            # Clear existing empty components
            for comp in composite.components:
                db.delete(comp)
        else:
            # Create new composite
            composite = Composite(
                material_id=blue_line.material_id,
                version=1,
                origin=CompositeOrigin.CALCULATED,
                composite_type=CompositeType.Z1,
                status=CompositeStatus.DRAFT,
                source_documents=pending_docs,
                extraction_confidence=confidence,
                composite_metadata={
                    "extraction_method": extraction_method,
                    "extraction_date": datetime.utcnow().isoformat(),
                    "source_blue_line": blue_line_id
                },
                notes=f"Extracted from {len(pdf_paths)} document(s) with {confidence:.1f}% confidence"
            )
            db.add(composite)
            db.flush()
        
        # Add components (validate required fields)
        for comp_data in components:
            # Validate required fields
            if not comp_data.get('component_name'):
                logger.warning(f"Skipping component without name: {comp_data}")
                continue
            
            component = CompositeComponent(
                cas_number=comp_data.get('cas_number') or None,
                component_name=comp_data['component_name'],
                percentage=comp_data.get('percentage', 0.0),
                confidence_level=comp_data.get('confidence', confidence)
            )
            composite.components.append(component)
        
        # Update Blue Line to reference this composite
        if not blue_line.composite_id:
            blue_line.composite_id = composite.id
        
        # Clear pending documents from metadata
        if blue_line.calculation_metadata:
            blue_line.calculation_metadata.pop("pending_documents", None)
        
        db.commit()
        db.refresh(composite)
        
        return {
            "composite_id": composite.id,
            "blue_line_id": blue_line_id,
            "material_id": blue_line.material_id,
            "components_count": len(components),
            "extraction_confidence": confidence,
            "extraction_method": extraction_method,
            "status": "extracted"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting composite from Blue Line: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting composite: {str(e)}"
        )


@router.post("/{blue_line_id}/create-composite", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_composite_z1(
    blue_line_id: int,
    db: Session = Depends(get_db)
):
    """
    Create a composite Z1 (mockup) for a Blue Line.
    
    DEPRECATED: Use /extract-composite instead for AI extraction.
    This creates a mock composite with dummy data for testing purposes.
    """
    from app.models.composite import Composite, CompositeStatus, CompositeOrigin, CompositeComponent
    from app.models.blue_line import BlueLine
    from app.models.material import Material
    
    blue_line = db.query(BlueLine).filter(BlueLine.id == blue_line_id).first()
    if not blue_line:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blue Line {blue_line_id} not found"
        )
    
    # Check if composite already exists
    if blue_line.composite_id:
        existing_composite = db.query(Composite).filter(Composite.id == blue_line.composite_id).first()
        if existing_composite and existing_composite.components:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Composite already exists for Blue Line {blue_line_id} (ID: {existing_composite.id})"
            )
    
    material = db.query(Material).filter(Material.id == blue_line.material_id).first()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Material {blue_line.material_id} not found"
        )
    
    # Get CAS number from Blue Line responses
    cas_number = material.cas_number or "000-00-0"
    if blue_line.responses:
        cas_field = blue_line.responses.get("q3t1s2f23")
        if cas_field:
            if isinstance(cas_field, dict):
                cas_number = cas_field.get("value", cas_number)
            else:
                cas_number = str(cas_field)
    
    # Create mock composite with dummy components
    composite = Composite(
        material_id=blue_line.material_id,
        version=1,
        origin=CompositeOrigin.LAB,
        status=CompositeStatus.APPROVED,
        composite_metadata={
            "source": "blue_line_mockup",
            "blue_line_id": blue_line_id,
            "type": "Z1_MOCKUP",
            "generated_at": datetime.now().isoformat()
        },
        notes=f"Mock composite Z1 generated for Blue Line - {material.name}"
    )
    
    db.add(composite)
    db.flush()
    
    # Create mock components
    mock_components = [
        {
            "cas_number": cas_number,
            "component_name": f"{material.name.split()[0] if material.name else 'Main'} Component",
            "percentage": 92.5,
            "component_type": "COMPONENT"
        },
        {
            "cas_number": "000-00-1",
            "component_name": "Component A",
            "percentage": 5.2,
            "component_type": "COMPONENT"
        },
        {
            "cas_number": "000-00-2",
            "component_name": "Impurity B",
            "percentage": 2.3,
            "component_type": "IMPURITY"
        }
    ]
    
    for comp_data in mock_components:
        component = CompositeComponent(
            composite_id=composite.id,
            cas_number=comp_data["cas_number"],
            component_name=comp_data["component_name"],
            percentage=comp_data["percentage"],
            component_type=comp_data["component_type"]
        )
        db.add(component)
    
    # Update Blue Line to reference this composite
    if not blue_line.composite_id:
        blue_line.composite_id = composite.id
    
    db.commit()
    db.refresh(composite)
    
    return {
        "composite_id": composite.id,
        "blue_line_id": blue_line_id,
        "material_id": material.id,
        "components_count": len(mock_components),
        "message": "Composite Z1 mockup created successfully"
    }

