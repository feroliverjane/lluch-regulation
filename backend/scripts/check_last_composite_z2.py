#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para revisar el último composite Z2 creado y verificar si tiene comparación
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.material import Material
from app.models.composite import Composite, CompositeType
import json

# Use production database or test database
DB_URL = settings.DATABASE_URL
print(f"📁 Conectando a base de datos: {DB_URL}")

engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

def check_last_composite_z2():
    """Revisar el último composite Z2 y su metadata"""
    db = SessionLocal()
    
    try:
        # Buscar todos los composites Z2 ordenados por fecha de creación
        z2_composites = db.query(Composite).filter(
            Composite.composite_type == CompositeType.Z2
        ).order_by(Composite.created_at.desc()).all()
        
        if not z2_composites:
            print("⚠️  No se encontraron composites Z2 en la base de datos")
            return
        
        print("=" * 80)
        print(f"  🔍 ÚLTIMO COMPOSITE Z2 CREADO")
        print("=" * 80)
        
        latest_z2 = z2_composites[0]
        
        print(f"\n📦 Composite Z2 más reciente:")
        print(f"   - ID: {latest_z2.id}")
        print(f"   - Material ID: {latest_z2.material_id}")
        print(f"   - Versión: {latest_z2.version}")
        print(f"   - Estado: {latest_z2.status.value}")
        print(f"   - Creado: {latest_z2.created_at}")
        print(f"   - Componentes: {len(latest_z2.components)}")
        
        # Verificar material
        material = db.query(Material).filter(Material.id == latest_z2.material_id).first()
        if material:
            print(f"\n📋 Material asociado:")
            print(f"   - Código: {material.reference_code}")
            print(f"   - Nombre: {material.name}")
        
        # Revisar metadata
        if latest_z2.composite_metadata:
            print(f"\n📊 Metadata del composite:")
            metadata = latest_z2.composite_metadata
            
            if isinstance(metadata, dict):
                # Verificar si hay snapshot de Z1
                z1_snapshot = metadata.get("z1_snapshot")
                if z1_snapshot:
                    print(f"   ✅ Snapshot de Z1 encontrado: {len(z1_snapshot)} componentes")
                    print(f"\n   Componentes Z1 (primeros 5):")
                    for idx, comp in enumerate(z1_snapshot[:5], 1):
                        print(f"      {idx}. {comp.get('component_name', 'N/A')}: {comp.get('percentage', 0)}% (CAS: {comp.get('cas_number', 'N/A')})")
                else:
                    print(f"   ⚠️  NO hay snapshot de Z1 en metadata")
                
                # Mostrar otros campos
                print(f"\n   Otros campos en metadata:")
                for key, value in metadata.items():
                    if key != "z1_snapshot":
                        if isinstance(value, (list, dict)):
                            print(f"      - {key}: {type(value).__name__} con {len(value) if isinstance(value, list) else len(value.keys())} elementos")
                        else:
                            print(f"      - {key}: {value}")
            else:
                print(f"   ⚠️  Metadata no es un diccionario: {type(metadata)}")
        
        # Verificar componentes actuales (Z2)
        print(f"\n🧪 Componentes Z2 actuales (primeros 10):")
        for idx, comp in enumerate(latest_z2.components[:10], 1):
            print(f"   {idx}. {comp.component_name}: {comp.percentage}% (CAS: {comp.cas_number or 'N/A'})")
        
        # Verificar si hay otros composites Z2 para comparar
        if len(z2_composites) > 1:
            print(f"\n📊 Total de composites Z2 encontrados: {len(z2_composites)}")
        
    except Exception as e:
        print(f"\n❌ Error al consultar: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_last_composite_z2()


