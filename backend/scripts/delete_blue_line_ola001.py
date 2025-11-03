#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para eliminar SOLO la línea azul asociada a OLA001
No elimina el material ni otros datos relacionados
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.material import Material
from app.models.blue_line import BlueLine

# Use production database or test database
DB_URL = settings.DATABASE_URL
print(f"📁 Conectando a base de datos: {DB_URL}")

engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

def delete_blue_line_ola001():
    """Eliminar SOLO la línea azul asociada a OLA001"""
    db = SessionLocal()
    
    try:
        # 1. Buscar el material por código OLA001 o nombre específico
        material = db.query(Material).filter(
            or_(
                Material.reference_code == "OLA001",
                Material.reference_code.ilike("%OLA001%"),
                Material.name.ilike("%C.P.ORANGE OIL ALD.1,20% MIN%"),
                Material.name.ilike("%C.P.ORANGE OIL%"),
                Material.name.ilike("%ORANGE OIL%")
            )
        ).first()
        
        if not material:
            print("❌ No se encontró material con código OLA001.")
            print("   Buscado por: OLA001, C.P.ORANGE OIL ALD.1,20% MIN")
            return
        
        material_id = material.id
        material_code = material.reference_code
        print(f"\n🔍 Material encontrado: {material_code} - {material.name} (ID: {material_id})")
        
        # 2. Buscar y eliminar Blue Line asociada
        blue_line = db.query(BlueLine).filter(
            BlueLine.material_id == material_id
        ).first()
        
        if not blue_line:
            print("   ℹ️  No se encontró Blue Line asociada a este material.")
            return
        
        print(f"   🗑️  Eliminando Blue Line (ID: {blue_line.id}, Tipo: {blue_line.material_type})...")
        db.delete(blue_line)
        
        # Commit el cambio
        db.commit()
        
        print("\n✅ Línea azul de OLA001 eliminada exitosamente!")
        print("   El material y otros datos relacionados se mantienen intactos.")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error al eliminar: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("  🗑️  Eliminar Línea Azul de OLA001")
    print("=" * 60)
    
    delete_blue_line_ola001()

