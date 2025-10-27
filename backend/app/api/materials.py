from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.material import Material
from app.schemas.material import MaterialCreate, MaterialUpdate, MaterialResponse

router = APIRouter(prefix="/materials", tags=["materials"])


@router.post("", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
def create_material(material: MaterialCreate, db: Session = Depends(get_db)):
    """Create a new material"""
    # Check if reference code already exists
    existing = db.query(Material).filter(
        Material.reference_code == material.reference_code
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Material with reference code '{material.reference_code}' already exists"
        )
    
    db_material = Material(**material.model_dump())
    db.add(db_material)
    db.commit()
    db.refresh(db_material)
    
    return db_material


@router.get("", response_model=List[MaterialResponse])
def list_materials(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """List all materials"""
    query = db.query(Material)
    
    if active_only:
        query = query.filter(Material.is_active == True)
    
    materials = query.offset(skip).limit(limit).all()
    return materials


@router.get("/{material_id}", response_model=MaterialResponse)
def get_material(material_id: int, db: Session = Depends(get_db)):
    """Get a specific material by ID"""
    material = db.query(Material).filter(Material.id == material_id).first()
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Material {material_id} not found"
        )
    
    return material


@router.get("/reference/{reference_code}", response_model=MaterialResponse)
def get_material_by_reference(reference_code: str, db: Session = Depends(get_db)):
    """Get a material by reference code"""
    material = db.query(Material).filter(
        Material.reference_code == reference_code
    ).first()
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Material with reference '{reference_code}' not found"
        )
    
    return material


@router.put("/{material_id}", response_model=MaterialResponse)
def update_material(
    material_id: int,
    material_update: MaterialUpdate,
    db: Session = Depends(get_db)
):
    """Update a material"""
    material = db.query(Material).filter(Material.id == material_id).first()
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Material {material_id} not found"
        )
    
    # Update fields
    update_data = material_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(material, field, value)
    
    db.commit()
    db.refresh(material)
    
    return material


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_material(material_id: int, db: Session = Depends(get_db)):
    """Delete a material (soft delete by setting is_active=False)"""
    material = db.query(Material).filter(Material.id == material_id).first()
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Material {material_id} not found"
        )
    
    material.is_active = False
    db.commit()
    
    return None








