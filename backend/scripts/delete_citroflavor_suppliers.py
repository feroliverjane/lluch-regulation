#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para eliminar todas las parejas material-proveedor (MaterialSuppliers) 
asociadas a CITROFLAVOR BRASIL LTDA
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.material_supplier import MaterialSupplier
from app.models.material import Material

# Use production database or test database
DB_URL = settings.DATABASE_URL
print(f"📁 Conectando a base de datos: {DB_URL}")

engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

def delete_citroflavor_suppliers():
    """Eliminar todas las parejas material-proveedor de CITROFLAVOR BRASIL LTDA"""
    db = SessionLocal()
    
    try:
        # Buscar todos los MaterialSuppliers de CITROFLAVOR BRASIL LTDA
        suppliers = db.query(MaterialSupplier).filter(
            or_(
                MaterialSupplier.supplier_name.ilike("%CITROFLAVOR BRASIL LTDA%"),
                MaterialSupplier.supplier_name.ilike("%CITROFLAVOR%"),
                MaterialSupplier.supplier_code.ilike("%CITROFLAVOR%")
            )
        ).all()
        
        if not suppliers:
            print("✅ No se encontraron MaterialSuppliers de CITROFLAVOR BRASIL LTDA.")
            return
        
        print(f"\n🔍 Encontrados {len(suppliers)} MaterialSupplier(s) de CITROFLAVOR BRASIL LTDA:")
        
        for supplier in suppliers:
            # Obtener información del material asociado
            material = db.query(Material).filter(Material.id == supplier.material_id).first()
            material_code = material.reference_code if material else f"Material ID {supplier.material_id}"
            material_name = material.name if material else "N/A"
            
            print(f"\n   - MaterialSupplier ID: {supplier.id}")
            print(f"     Material: {material_code} - {material_name}")
            print(f"     Supplier: {supplier.supplier_name or supplier.supplier_code}")
            print(f"     Questionnaire ID: {supplier.questionnaire_id}")
            print(f"     Status: {supplier.status}")
            print(f"     Score: {supplier.validation_score}")
        
        print(f"\n🗑️  Eliminando {len(suppliers)} MaterialSupplier(s)...")
        
        for supplier in suppliers:
            db.delete(supplier)
        
        # Commit todos los cambios
        db.commit()
        
        print(f"\n✅ {len(suppliers)} MaterialSupplier(s) de CITROFLAVOR BRASIL LTDA eliminados exitosamente!")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error al eliminar: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("  🗑️  Eliminar MaterialSuppliers de CITROFLAVOR BRASIL LTDA")
    print("=" * 60)
    
    delete_citroflavor_suppliers()

