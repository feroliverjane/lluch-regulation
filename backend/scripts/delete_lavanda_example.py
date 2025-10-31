#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para eliminar el ejemplo de lavanda de la base de datos
Elimina: Material, Blue Line, Questionnaires, Composites, MaterialSuppliers relacionados
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
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

def delete_lavanda_example():
    """Eliminar todos los datos relacionados con LAVANDA9999"""
    db = SessionLocal()
    
    try:
        # 1. Buscar el material
        material = db.query(Material).filter(
            Material.reference_code == "LAVANDA9999"
        ).first()
        
        if not material:
            print("✅ No se encontró material LAVANDA9999. Ya está limpio.")
            return
        
        material_id = material.id
        print(f"\n🔍 Material encontrado: {material.reference_code} (ID: {material_id})")
        
        # 2. Eliminar MaterialSuppliers relacionados
        suppliers = db.query(MaterialSupplier).filter(
            MaterialSupplier.material_id == material_id
        ).all()
        if suppliers:
            print(f"   🗑️  Eliminando {len(suppliers)} MaterialSupplier(s)...")
            for supplier in suppliers:
                db.delete(supplier)
        
        # 3. Eliminar Blue Line si existe
        blue_line = db.query(BlueLine).filter(
            BlueLine.material_id == material_id
        ).first()
        if blue_line:
            print(f"   🗑️  Eliminando Blue Line (ID: {blue_line.id})...")
            db.delete(blue_line)
        
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
        
        print("\n✅ Ejemplo de lavanda eliminado exitosamente!")
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
    print("  🧹 Limpieza: Eliminar Ejemplo Lavanda (LAVANDA9999)")
    print("=" * 60)
    
    confirm = input("\n⚠️  ¿Estás seguro de que quieres eliminar LAVANDA9999? (s/N): ")
    if confirm.lower() in ['s', 'si', 'sí', 'y', 'yes']:
        delete_lavanda_example()
    else:
        print("❌ Operación cancelada.")

