#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para eliminar el ejemplo de naranja (Orange Oil) de la base de datos
Elimina: Material, Blue Line, Questionnaires, Composites, MaterialSuppliers relacionados
Busca por código OLA001 o nombre que contenga "C.P.ORANGE OIL ALD.1,20% MIN"
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.core.config import settings
from app.models.material import Material
from app.models.blue_line import BlueLine
from app.models.questionnaire import Questionnaire
from app.models.composite import Composite
from app.models.material_supplier import MaterialSupplier

# Use production database or test database
DB_URL = settings.DATABASE_URL
print(f"📁 Conectando a base de datos: {DB_URL}")

engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

def delete_orange_oil_example():
    """Eliminar todos los datos relacionados con Orange Oil (OLA001)"""
    db = SessionLocal()
    
    try:
        # 1. Buscar el material por código OLA001 o nombre específico
        material = db.query(Material).filter(
            or_(
                Material.reference_code == "OLA001",
                Material.reference_code.ilike("%OLA001%"),
                Material.name.ilike("%C.P.ORANGE OIL ALD.1,20% MIN%"),
                Material.name.ilike("%C.P.ORANGE OIL%"),
                Material.name.ilike("%ORANGE OIL%"),
                Material.name.ilike("%NARANJA%")
            )
        ).first()
        
        if not material:
            print("✅ No se encontró material de naranja con código OLA001.")
            print("   Buscado por: OLA001, C.P.ORANGE OIL ALD.1,20% MIN")
            
            # Mostrar todos los materiales que contengan "orange" o "naranja" para referencia
            all_materials = db.query(Material).filter(
                or_(
                    Material.reference_code.ilike("%ORANGE%"),
                    Material.name.ilike("%ORANGE%"),
                    Material.name.ilike("%NARANJA%")
                )
            ).all()
            
            if all_materials:
                print("\n📋 Materiales relacionados encontrados:")
                for m in all_materials:
                    print(f"   - {m.reference_code}: {m.name} (ID: {m.id})")
            return
        
        material_id = material.id
        material_code = material.reference_code
        print(f"\n🔍 Material encontrado: {material_code} - {material.name} (ID: {material_id})")
        
        # 2. Eliminar MaterialSuppliers relacionados
        suppliers = db.query(MaterialSupplier).filter(
            MaterialSupplier.material_id == material_id
        ).all()
        if suppliers:
            print(f"   🗑️  Eliminando {len(suppliers)} MaterialSupplier(s)...")
            for supplier in suppliers:
                db.delete(supplier)
        
        # 3. Eliminar Blue Line si existe
        blue_lines = db.query(BlueLine).filter(
            BlueLine.material_id == material_id
        ).all()
        if blue_lines:
            print(f"   🗑️  Eliminando {len(blue_lines)} Blue Line(s)...")
            for bl in blue_lines:
                print(f"      - Blue Line ID: {bl.id}, Tipo: {bl.material_type}")
                db.delete(bl)
        else:
            print("   ℹ️  No se encontró Blue Line asociada")
        
        # 4. Eliminar Questionnaires relacionados
        questionnaires = db.query(Questionnaire).filter(
            Questionnaire.material_id == material_id
        ).all()
        if questionnaires:
            print(f"   🗑️  Eliminando {len(questionnaires)} Questionnaire(s)...")
            for q in questionnaires:
                db.delete(q)
        
        # 5. Eliminar Composites relacionados
        composites = db.query(Composite).filter(
            Composite.material_id == material_id
        ).all()
        if composites:
            print(f"   🗑️  Eliminando {len(composites)} Composite(s)...")
            for comp in composites:
                db.delete(comp)
        
        # 6. Finalmente, eliminar el Material
        print(f"   🗑️  Eliminando Material (ID: {material_id})...")
        db.delete(material)
        
        # Commit todos los cambios
        db.commit()
        
        print("\n✅ Ejemplo de naranja (OLA001) eliminado exitosamente!")
        print("   Puedes volver a importar el cuestionario JSON para probar.")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error al eliminar: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("  🧹 Limpieza: Eliminar Ejemplo Orange Oil (OLA001)")
    print("=" * 60)
    
    confirm = input("\n⚠️  ¿Estás seguro de que quieres eliminar el material OLA001 y su línea azul? (s/N): ")
    if confirm.lower() in ['s', 'si', 'sí', 'y', 'yes']:
        delete_orange_oil_example()
    else:
        print("❌ Operación cancelada.")
