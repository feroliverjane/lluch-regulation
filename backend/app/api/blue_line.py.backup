from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

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

router = APIRouter(prefix="/blue-line", tags=["blue-line"])


@router.post("/calculate", response_model=BlueLineResponse, status_code=status.HTTP_201_CREATED)
async def calculate_blue_line(
    request: BlueLineCalculateRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate Blue Line for a material-supplier pair
    
    This endpoint:
    1. Checks eligibility (purchase history, approval states)
    2. Calculates all 446 fields based on configured logic
    3. Creates or updates the Blue Line record
    """
    calculator = BlueLineCalculator(db)
    
    try:
        blue_line = await calculator.calculate_blue_line(
            material_id=request.material_id,
            supplier_code=request.supplier_code,
            force_recalculate=request.force_recalculate
        )
        
        if not blue_line:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Material-supplier pair is not eligible for Blue Line or calculation failed"
            )
        
        return blue_line
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/material/{material_id}", response_model=List[BlueLineResponse])
def get_blue_lines_by_material(
    material_id: int,
    db: Session = Depends(get_db)
):
    """Get all Blue Line records for a material"""
    blue_lines = db.query(BlueLine).filter(
        BlueLine.material_id == material_id
    ).all()
    
    return blue_lines


@router.get("/material/{material_id}/supplier/{supplier_code}", response_model=BlueLineResponse)
def get_blue_line_by_material_supplier(
    material_id: int,
    supplier_code: str,
    db: Session = Depends(get_db)
):
    """Get specific Blue Line for material-supplier pair"""
    blue_line = db.query(BlueLine).filter(
        BlueLine.material_id == material_id,
        BlueLine.supplier_code == supplier_code
    ).first()
    
    if not blue_line:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blue Line not found for material {material_id}, supplier {supplier_code}"
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
    """
    calculator = BlueLineCalculator(db)
    
    # Get all active materials with supplier codes
    materials = db.query(Material).filter(
        Material.is_active == True,
        Material.supplier_code.isnot(None)
    ).all()
    
    eligibility_results = []
    
    for material in materials:
        is_eligible, details = await calculator.check_eligibility(
            material.id,
            material.supplier_code
        )
        
        eligibility_results.append(
            BlueLineEligibilityCheck(
                material_id=material.id,
                supplier_code=material.supplier_code,
                is_eligible=is_eligible,
                reasons=details.get("reasons", []),
                has_purchase_history=details.get("has_purchase_history", False),
                regulatory_status_ok=details.get("regulatory_status_ok", False),
                technical_status_ok=details.get("technical_status_ok", False),
                purchase_date=material.last_purchase_date
            )
        )
    
    return eligibility_results


@router.get("/check-eligibility/material/{material_id}/supplier/{supplier_code}", response_model=BlueLineEligibilityCheck)
async def check_eligibility(
    material_id: int,
    supplier_code: str,
    db: Session = Depends(get_db)
):
    """
    Check if a specific material-supplier pair is eligible for Blue Line
    """
    calculator = BlueLineCalculator(db)
    
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Material {material_id} not found"
        )
    
    is_eligible, details = await calculator.check_eligibility(material_id, supplier_code)
    
    return BlueLineEligibilityCheck(
        material_id=material_id,
        supplier_code=supplier_code,
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

