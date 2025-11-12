#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar que la línea azul de OLA001 fue eliminada
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

def verify_deletion():
    """Verificar que la línea azul de OLA001 fue eliminada"""
    db = SessionLocal()
    
    try:
        # 1. Buscar el material OLA001
        material = db.query(Material).filter(
            or_(
                Material.reference_code == "OLA001",
                Material.reference_code.ilike("%OLA001%"),
                Material.name.ilike("%C.P.ORANGE OIL ALD.1,20% MIN%")
            )
        ).first()
        
        if not material:
            print("❌ No se encontró material OLA001")
            return
        
        print(f"\n✅ Material encontrado:")
        print(f"   - Código: {material.reference_code}")
        print(f"   - Nombre: {material.name}")
        print(f"   - ID: {material.id}")
        
        # 2. Buscar línea azul asociada
        blue_line = db.query(BlueLine).filter(
            BlueLine.material_id == material.id
        ).first()
        
        if blue_line:
            print(f"\n❌ ¡ATENCIÓN! Todavía existe una línea azul:")
            print(f"   - Blue Line ID: {blue_line.id}")
            print(f"   - Tipo: {blue_line.material_type}")
            print(f"   - Material ID: {blue_line.material_id}")
        else:
            print(f"\n✅ Confirmado: NO existe línea azul asociada a OLA001")
            print(f"   La línea azul fue eliminada correctamente.")
        
        # 3. Mostrar todas las líneas azules en la base de datos para referencia
        all_blue_lines = db.query(BlueLine).all()
        print(f"\n📊 Total de líneas azules en la base de datos: {len(all_blue_lines)}")
        if all_blue_lines:
            print("   Líneas azules existentes:")
            for bl in all_blue_lines:
                mat = db.query(Material).filter(Material.id == bl.material_id).first()
                mat_code = mat.reference_code if mat else f"Material ID {bl.material_id}"
                print(f"      - Blue Line ID {bl.id}: Material {mat_code} (Tipo: {bl.material_type})")
        
    except Exception as e:
        print(f"\n❌ Error al verificar: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("  🔍 Verificar Eliminación de Línea Azul OLA001")
    print("=" * 60)
    
    verify_deletion()









