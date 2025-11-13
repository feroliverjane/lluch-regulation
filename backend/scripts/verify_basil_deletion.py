#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar que todos los datos relacionados con basílico fueron eliminados
(BASC005 y BASIL0003)
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
from app.models.composite import Composite, CompositeComponent
from app.models.questionnaire import Questionnaire
from app.models.material_supplier import MaterialSupplier
from app.models.chromatographic_analysis import ChromatographicAnalysis
from app.models.approval_workflow import ApprovalWorkflow

# Use production database or test database
DB_URL = settings.DATABASE_URL
print(f"📁 Conectando a base de datos: {DB_URL}")

engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

def verify_basil_deletion():
    """Verificar que todos los datos relacionados con basílico fueron eliminados"""
    db = SessionLocal()
    
    try:
        basil_codes = ["BASC005", "BASIL0003"]
        
        print("=" * 80)
        print("  🔍 VERIFICACIÓN DE ELIMINACIÓN DE MATERIALES DE BASÍLICO")
        print("=" * 80)
        print()
        
        all_clean = True
        
        for material_code in basil_codes:
            print(f"\n📦 Verificando material: {material_code}")
            print("-" * 80)
            
            # 1. Buscar el material
            material = db.query(Material).filter(
                Material.reference_code == material_code
            ).first()
            
            if material:
                print(f"   ❌ Material encontrado: {material.reference_code} - {material.name} (ID: {material.id})")
                all_clean = False
                
                material_id = material.id
                
                # Verificar todos los componentes relacionados
                # 2. MaterialSuppliers
                suppliers = db.query(MaterialSupplier).filter(
                    MaterialSupplier.material_id == material_id
                ).all()
                if suppliers:
                    print(f"   ❌ MaterialSuppliers encontrados: {len(suppliers)}")
                    for s in suppliers:
                        print(f"      - ID: {s.id}, Supplier: {s.supplier_code}")
                    all_clean = False
                else:
                    print(f"   ✅ No hay MaterialSuppliers")
                
                # 3. Blue Lines
                blue_lines = db.query(BlueLine).filter(
                    BlueLine.material_id == material_id
                ).all()
                if blue_lines:
                    print(f"   ❌ Blue Lines encontradas: {len(blue_lines)}")
                    for bl in blue_lines:
                        print(f"      - ID: {bl.id}, Tipo: {bl.material_type}")
                    all_clean = False
                else:
                    print(f"   ✅ No hay Blue Lines")
                
                # 4. Composites
                composites = db.query(Composite).filter(
                    Composite.material_id == material_id
                ).all()
                if composites:
                    print(f"   ❌ Composites encontrados: {len(composites)}")
                    for comp in composites:
                        print(f"      - ID: {comp.id}, Version: {comp.version}, Status: {comp.status}")
                        
                        # Verificar componentes del composite
                        components = db.query(CompositeComponent).filter(
                            CompositeComponent.composite_id == comp.id
                        ).all()
                        if components:
                            print(f"         Componentes: {len(components)}")
                            all_clean = False
                    all_clean = False
                else:
                    print(f"   ✅ No hay Composites")
                
                # 5. Questionnaires
                questionnaires = db.query(Questionnaire).filter(
                    Questionnaire.material_id == material_id
                ).all()
                if questionnaires:
                    print(f"   ❌ Questionnaires encontrados: {len(questionnaires)}")
                    for q in questionnaires:
                        print(f"      - ID: {q.id}, Status: {q.status}, Version: {q.version}")
                    all_clean = False
                else:
                    print(f"   ✅ No hay Questionnaires")
                
                # 6. Chromatographic Analyses
                analyses = db.query(ChromatographicAnalysis).filter(
                    ChromatographicAnalysis.material_id == material_id
                ).all()
                if analyses:
                    print(f"   ❌ Chromatographic Analyses encontrados: {len(analyses)}")
                    for a in analyses:
                        print(f"      - ID: {a.id}, File: {a.filename}")
                    all_clean = False
                else:
                    print(f"   ✅ No hay Chromatographic Analyses")
                
                # 7. ApprovalWorkflows (a través de composites)
                workflow_count = 0
                for comp in composites:
                    workflows = db.query(ApprovalWorkflow).filter(
                        ApprovalWorkflow.composite_id == comp.id
                    ).all()
                    if workflows:
                        workflow_count += len(workflows)
                        print(f"   ❌ ApprovalWorkflows encontrados: {len(workflows)} para Composite {comp.id}")
                        for wf in workflows:
                            print(f"      - ID: {wf.id}, Status: {wf.status}")
                        all_clean = False
                
                if workflow_count == 0:
                    print(f"   ✅ No hay ApprovalWorkflows")
                
            else:
                print(f"   ✅ Material {material_code} no encontrado (eliminado correctamente)")
        
        # Resumen final
        print("\n" + "=" * 80)
        if all_clean:
            print("  ✅ VERIFICACIÓN COMPLETADA - TODO ELIMINADO CORRECTAMENTE")
            print("=" * 80)
            print("\n✅ Todos los materiales de basílico y sus datos relacionados han sido eliminados.")
            print("   Puedes proceder a probar el sistema importando cuestionarios JSON.")
        else:
            print("  ⚠️  VERIFICACIÓN COMPLETADA - SE ENCONTRARON DATOS PENDIENTES")
            print("=" * 80)
            print("\n⚠️  Aún existen datos relacionados con materiales de basílico.")
            print("   Ejecuta el script delete_basil_materials.py para eliminarlos.")
        
        # Mostrar resumen de materiales existentes
        print("\n📊 Resumen de materiales en la base de datos:")
        all_materials = db.query(Material).all()
        print(f"   Total de materiales: {len(all_materials)}")
        if all_materials:
            print("   Materiales existentes:")
            for mat in all_materials[:20]:  # Mostrar primeros 20
                print(f"      - {mat.reference_code}: {mat.name}")
            if len(all_materials) > 20:
                print(f"      ... y {len(all_materials) - 20} más")
        
    except Exception as e:
        print(f"\n❌ Error al verificar: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_basil_deletion()


