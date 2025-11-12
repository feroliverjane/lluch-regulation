#!/usr/bin/env python3
"""
Script para eliminar todos los datos relacionados con materiales de basílico
(BASC005 y BASIL0003) para poder probar el sistema desde cero.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.material import Material
from app.models.blue_line import BlueLine
from app.models.composite import Composite, CompositeComponent
from app.models.questionnaire import Questionnaire
from app.models.material_supplier import MaterialSupplier
from app.models.chromatographic_analysis import ChromatographicAnalysis
from app.models.approval_workflow import ApprovalWorkflow

# Create database connection
DB_URL = os.getenv("DATABASE_URL", settings.DATABASE_URL)
print(f"📁 Conectando a base de datos: {DB_URL}")

engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

def delete_basil_materials():
    """Eliminar todos los datos relacionados con materiales de basílico"""
    db = SessionLocal()
    
    try:
        # Materiales a eliminar
        basil_codes = ["BASC005", "BASIL0003"]
        
        print("=" * 80)
        print("  🗑️  ELIMINACIÓN DE MATERIALES DE BASÍLICO")
        print("=" * 80)
        print()
        
        for material_code in basil_codes:
            print(f"\n📦 Procesando material: {material_code}")
            print("-" * 80)
            
            # 1. Buscar el material
            material = db.query(Material).filter(
                Material.reference_code == material_code
            ).first()
            
            if not material:
                print(f"   ℹ️  Material {material_code} no encontrado. Saltando...")
                continue
            
            material_id = material.id
            print(f"   ✅ Material encontrado: {material.reference_code} - {material.name} (ID: {material_id})")
            
            # 2. Eliminar MaterialSuppliers relacionados
            suppliers = db.query(MaterialSupplier).filter(
                MaterialSupplier.material_id == material_id
            ).all()
            if suppliers:
                print(f"   🗑️  Eliminando {len(suppliers)} MaterialSupplier(s)...")
                for supplier in suppliers:
                    print(f"      - MaterialSupplier ID: {supplier.id}, Supplier: {supplier.supplier_code}")
                    db.delete(supplier)
            else:
                print("   ℹ️  No se encontraron MaterialSuppliers")
            
            # 3. Eliminar ApprovalWorkflows relacionados (a través de composites)
            composites = db.query(Composite).filter(
                Composite.material_id == material_id
            ).all()
            
            workflow_count = 0
            for comp in composites:
                workflows = db.query(ApprovalWorkflow).filter(
                    ApprovalWorkflow.composite_id == comp.id
                ).all()
                for wf in workflows:
                    print(f"      - ApprovalWorkflow ID: {wf.id}, Status: {wf.status}")
                    db.delete(wf)
                    workflow_count += 1
            
            if workflow_count > 0:
                print(f"   🗑️  Eliminando {workflow_count} ApprovalWorkflow(s)...")
            else:
                print("   ℹ️  No se encontraron ApprovalWorkflows")
            
            # 4. Eliminar CompositeComponents relacionados
            component_count = 0
            for comp in composites:
                components = db.query(CompositeComponent).filter(
                    CompositeComponent.composite_id == comp.id
                ).all()
                for comp_comp in components:
                    db.delete(comp_comp)
                    component_count += 1
            
            if component_count > 0:
                print(f"   🗑️  Eliminando {component_count} CompositeComponent(s)...")
            
            # 5. Eliminar Composites relacionados
            if composites:
                print(f"   🗑️  Eliminando {len(composites)} Composite(s)...")
                for comp in composites:
                    print(f"      - Composite ID: {comp.id}, Version: {comp.version}, Status: {comp.status}")
                    db.delete(comp)
            else:
                print("   ℹ️  No se encontraron Composites")
            
            # 6. Eliminar Blue Lines relacionadas
            blue_lines = db.query(BlueLine).filter(
                BlueLine.material_id == material_id
            ).all()
            if blue_lines:
                print(f"   🗑️  Eliminando {len(blue_lines)} Blue Line(s)...")
                for bl in blue_lines:
                    print(f"      - Blue Line ID: {bl.id}, Tipo: {bl.material_type}")
                    db.delete(bl)
            else:
                print("   ℹ️  No se encontraron Blue Lines")
            
            # 7. Eliminar Questionnaires relacionados
            questionnaires = db.query(Questionnaire).filter(
                Questionnaire.material_id == material_id
            ).all()
            if questionnaires:
                print(f"   🗑️  Eliminando {len(questionnaires)} Questionnaire(s)...")
                for q in questionnaires:
                    print(f"      - Questionnaire ID: {q.id}, Status: {q.status}, Version: {q.version}")
                    db.delete(q)
            else:
                print("   ℹ️  No se encontraron Questionnaires")
            
            # 8. Eliminar Chromatographic Analyses relacionados
            analyses = db.query(ChromatographicAnalysis).filter(
                ChromatographicAnalysis.material_id == material_id
            ).all()
            if analyses:
                print(f"   🗑️  Eliminando {len(analyses)} ChromatographicAnalysis(es)...")
                for analysis in analyses:
                    print(f"      - Analysis ID: {analysis.id}, File: {analysis.filename}")
                    db.delete(analysis)
            else:
                print("   ℹ️  No se encontraron Chromatographic Analyses")
            
            # 9. Finalmente, eliminar el Material
            print(f"   🗑️  Eliminando Material (ID: {material_id})...")
            db.delete(material)
            
            print(f"   ✅ Material {material_code} eliminado completamente")
        
        # Commit todos los cambios
        db.commit()
        
        print("\n" + "=" * 80)
        print("  ✅ ELIMINACIÓN COMPLETADA")
        print("=" * 80)
        print("\nTodos los materiales de basílico y sus datos relacionados han sido eliminados.")
        print("Ahora puedes volver a importar cuestionarios JSON para probar el sistema.")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error al eliminar: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    delete_basil_materials()

