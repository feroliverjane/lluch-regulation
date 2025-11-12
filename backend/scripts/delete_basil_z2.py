#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para eliminar el composite Z2 del basílico y restaurarlo a Z1
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.material import Material
from app.models.composite import Composite, CompositeType, CompositeComponent
import json

# Use production database or test database
DB_URL = settings.DATABASE_URL
print(f"📁 Conectando a base de datos: {DB_URL}")

engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

def delete_basil_z2():
    """Eliminar composite Z2 del basílico y restaurar a Z1 si hay snapshot"""
    db = SessionLocal()
    
    try:
        # Buscar el material BASIL0003
        material = db.query(Material).filter(
            Material.reference_code == "BASIL0003"
        ).first()
        
        if not material:
            print("❌ Material BASIL0003 no encontrado en la base de datos")
            return
        
        print("=" * 80)
        print(f"  🗑️  ELIMINAR COMPOSITE Z2 DE BASIL0003")
        print("=" * 80)
        print(f"\n✅ Material encontrado:")
        print(f"   - Código: {material.reference_code}")
        print(f"   - Nombre: {material.name}")
        print(f"   - ID: {material.id}")
        
        # Buscar composite Z2 para este material
        z2_composite = db.query(Composite).filter(
            Composite.material_id == material.id,
            Composite.composite_type == CompositeType.Z2
        ).first()
        
        if not z2_composite:
            print(f"\n⚠️  No se encontró composite Z2 para BASIL0003")
            
            # Buscar cualquier composite
            all_composites = db.query(Composite).filter(
                Composite.material_id == material.id
            ).all()
            
            if all_composites:
                print(f"\n📦 Composites encontrados:")
                for comp in all_composites:
                    print(f"   - ID: {comp.id}, Tipo: {comp.composite_type.value if comp.composite_type else 'N/A'}, Versión: {comp.version}")
            else:
                print(f"\n⚠️  No se encontraron composites para este material")
            
            return
        
        print(f"\n📦 Composite Z2 encontrado:")
        print(f"   - ID: {z2_composite.id}")
        print(f"   - Versión: {z2_composite.version}")
        print(f"   - Componentes: {len(z2_composite.components)}")
        
        # Verificar si hay snapshot de Z1 en metadata
        z1_snapshot = None
        if z2_composite.composite_metadata and isinstance(z2_composite.composite_metadata, dict):
            z1_snapshot = z2_composite.composite_metadata.get("z1_snapshot")
        
        if z1_snapshot:
            print(f"\n✅ Snapshot de Z1 encontrado en metadata ({len(z1_snapshot)} componentes)")
            print(f"\n🔄 Restaurando composite a Z1 desde snapshot...")
            
            # Eliminar componentes actuales
            for component in z2_composite.components:
                db.delete(component)
            
            # Restaurar componentes desde snapshot
            for comp_data in z1_snapshot:
                component = CompositeComponent(
                    composite_id=z2_composite.id,
                    cas_number=comp_data.get("cas_number"),
                    component_name=comp_data.get("component_name"),
                    percentage=comp_data.get("percentage"),
                    component_type=comp_data.get("component_type", "COMPONENT")
                )
                z2_composite.components.append(component)
            
            # Cambiar tipo de vuelta a Z1
            z2_composite.composite_type = CompositeType.Z1
            from app.models.composite import CompositeOrigin
            z2_composite.origin = CompositeOrigin.CALCULATED  # Restaurar origen original
            
            # Limpiar metadata relacionada con Z2
            if z2_composite.composite_metadata:
                z2_composite.composite_metadata.pop("import_source", None)
                z2_composite.composite_metadata.pop("import_filename", None)
                z2_composite.composite_metadata.pop("import_date", None)
                z2_composite.composite_metadata.pop("total_percentage", None)
                # Mantener z1_snapshot por si acaso
            
            z2_composite.notes = f"Restaurado desde Z2. Originalmente extraído de documentos."
            
            db.commit()
            db.refresh(z2_composite)
            
            print(f"✅ Composite restaurado a Z1 exitosamente")
            print(f"   - Componentes restaurados: {len(z2_composite.components)}")
        else:
            print(f"\n⚠️  No se encontró snapshot de Z1 en metadata")
            print(f"   Eliminando completamente el composite Z2...")
            
            # Eliminar componentes
            for component in z2_composite.components:
                db.delete(component)
            
            # Eliminar composite
            db.delete(z2_composite)
            db.commit()
            
            print(f"✅ Composite Z2 eliminado completamente")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error al procesar: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    delete_basil_z2()

