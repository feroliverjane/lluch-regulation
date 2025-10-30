from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.models.material_supplier import MaterialSupplier
from app.models.questionnaire import Questionnaire, QuestionnaireStatus
from app.models.blue_line import BlueLine
from app.models.material import Material
from app.schemas.material_supplier import (
    MaterialSupplierCreate,
    MaterialSupplierUpdate,
    MaterialSupplierResponse,
    AcceptMismatchesRequest,
)
from app.services.material_supplier_comparison import MaterialSupplierComparisonService

router = APIRouter(prefix="/material-suppliers", tags=["material-suppliers"])


@router.post("", response_model=MaterialSupplierResponse, status_code=status.HTTP_201_CREATED)
def create_material_supplier(
    request: MaterialSupplierCreate,
    db: Session = Depends(get_db)
):
    """
    Create a MaterialSupplier from an accepted questionnaire.
    
    This endpoint:
    1. Validates the questionnaire exists
    2. Gets the Blue Line for the material
    3. Performs comparison if Blue Line exists
    4. Creates MaterialSupplier record
    5. Updates questionnaire status to APPROVED
    """
    # Get questionnaire
    questionnaire = db.query(Questionnaire).filter(
        Questionnaire.id == request.questionnaire_id
    ).first()
    
    if not questionnaire:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Questionnaire {request.questionnaire_id} not found"
        )
    
    # Check if MaterialSupplier already exists for this questionnaire
    existing = db.query(MaterialSupplier).filter(
        MaterialSupplier.questionnaire_id == request.questionnaire_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"MaterialSupplier already exists for questionnaire {request.questionnaire_id}"
        )
    
    # Get material
    material = db.query(Material).filter(Material.id == questionnaire.material_id).first()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Material {questionnaire.material_id} not found"
        )
    
    # Get Blue Line for this material
    blue_line = db.query(BlueLine).filter(
        BlueLine.material_id == questionnaire.material_id
    ).first()
    
    # Perform comparison
    comparison_result = MaterialSupplierComparisonService.compare_questionnaire_with_blue_line(
        questionnaire, blue_line
    )
    
    # Extract supplier name from questionnaire
    supplier_name = None
    if questionnaire.responses:
        supplier_field = questionnaire.responses.get("q3t1s2f15")
        if supplier_field:
            if isinstance(supplier_field, dict):
                supplier_name = supplier_field.get("value", "")
            else:
                supplier_name = str(supplier_field)
    
    # Build mismatch_fields list from comparison result
    mismatch_fields = []
    for mismatch in comparison_result.mismatches:
        mismatch_fields.append({
            "field_code": mismatch.field_code,
            "field_name": mismatch.field_name,
            "expected_value": mismatch.expected_value,
            "actual_value": mismatch.actual_value,
            "severity": mismatch.severity,
            "accepted": mismatch.field_code in request.accepted_mismatches
        })
    
    # Create MaterialSupplier
    material_supplier = MaterialSupplier(
        material_id=questionnaire.material_id,
        questionnaire_id=questionnaire.id,
        blue_line_id=blue_line.id if blue_line else None,
        supplier_code=questionnaire.supplier_code,
        supplier_name=supplier_name,
        status="ACTIVE",
        validation_score=comparison_result.score,
        mismatch_fields=mismatch_fields,
        accepted_mismatches=request.accepted_mismatches,
        validated_at=datetime.utcnow()
    )
    
    db.add(material_supplier)
    
    # Update questionnaire status to APPROVED
    questionnaire.status = QuestionnaireStatus.APPROVED
    questionnaire.approved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(material_supplier)
    
    return material_supplier


@router.get("/{material_supplier_id}", response_model=MaterialSupplierResponse)
def get_material_supplier(
    material_supplier_id: int,
    db: Session = Depends(get_db)
):
    """Get MaterialSupplier by ID"""
    material_supplier = db.query(MaterialSupplier).filter(
        MaterialSupplier.id == material_supplier_id
    ).first()
    
    if not material_supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MaterialSupplier {material_supplier_id} not found"
        )
    
    return material_supplier


@router.get("/by-material/{material_id}", response_model=List[MaterialSupplierResponse])
def get_material_suppliers_by_material(
    material_id: int,
    db: Session = Depends(get_db)
):
    """Get all MaterialSuppliers for a specific material"""
    material_suppliers = db.query(MaterialSupplier).filter(
        MaterialSupplier.material_id == material_id
    ).order_by(MaterialSupplier.created_at.desc()).all()
    
    return material_suppliers


@router.post("/{material_supplier_id}/accept-mismatches", response_model=MaterialSupplierResponse)
def accept_mismatches(
    material_supplier_id: int,
    request: AcceptMismatchesRequest,
    db: Session = Depends(get_db)
):
    """Accept specific mismatches for a MaterialSupplier"""
    material_supplier = db.query(MaterialSupplier).filter(
        MaterialSupplier.id == material_supplier_id
    ).first()
    
    if not material_supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MaterialSupplier {material_supplier_id} not found"
        )
    
    # Update accepted mismatches
    current_accepted = set(material_supplier.accepted_mismatches or [])
    new_accepted = set(request.accepted_mismatches)
    material_supplier.accepted_mismatches = list(current_accepted.union(new_accepted))
    
    # Update mismatch_fields to mark accepted ones
    if material_supplier.mismatch_fields:
        for mismatch in material_supplier.mismatch_fields:
            if mismatch.get("field_code") in request.accepted_mismatches:
                mismatch["accepted"] = True
    
    db.commit()
    db.refresh(material_supplier)
    
    return material_supplier


@router.put("/{material_supplier_id}", response_model=MaterialSupplierResponse)
def update_material_supplier(
    material_supplier_id: int,
    request: MaterialSupplierUpdate,
    db: Session = Depends(get_db)
):
    """Update MaterialSupplier"""
    material_supplier = db.query(MaterialSupplier).filter(
        MaterialSupplier.id == material_supplier_id
    ).first()
    
    if not material_supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MaterialSupplier {material_supplier_id} not found"
        )
    
    if request.status is not None:
        material_supplier.status = request.status.value
    
    if request.accepted_mismatches is not None:
        material_supplier.accepted_mismatches = request.accepted_mismatches
        # Update mismatch_fields
        if material_supplier.mismatch_fields:
            accepted_set = set(request.accepted_mismatches)
            for mismatch in material_supplier.mismatch_fields:
                mismatch["accepted"] = mismatch.get("field_code") in accepted_set
    
    db.commit()
    db.refresh(material_supplier)
    
    return material_supplier

