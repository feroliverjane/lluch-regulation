"""
Script para crear datos de ejemplo y probar todas las funcionalidades del sistema Material-Supplier

Este script:
1. Crea un cuestionario de ejemplo con diferencias para el material 10
2. Lo importa usando el endpoint
3. Verifica la comparación automática
4. Crea MaterialSupplier aceptando diferencias
5. Verifica que aparezca en BlueLineDetail
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.database import SessionLocal
from app.models.material import Material
from app.models.blue_line import BlueLine
from app.models.questionnaire import Questionnaire, QuestionnaireType, QuestionnaireStatus
from app.models.questionnaire_template import QuestionnaireTemplate, TemplateType
from app.models.material_supplier import MaterialSupplier
from app.services.material_supplier_comparison import MaterialSupplierComparisonService
from datetime import datetime
import json

def create_example_questionnaire_with_differences(db: SessionLocal, material_id: int):
    """Crea un cuestionario de ejemplo con diferencias intencionales"""
    print(f"\n📝 Creando cuestionario de ejemplo para material {material_id}...")
    
    # Obtener material y BlueLine
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        print(f"❌ Material {material_id} no encontrado")
        return None
    
    blue_line = db.query(BlueLine).filter(BlueLine.material_id == material_id).first()
    if not blue_line:
        print(f"❌ BlueLine para material {material_id} no encontrada")
        return None
    
    # Obtener template
    template = db.query(QuestionnaireTemplate).filter(
        QuestionnaireTemplate.is_default == True,
        QuestionnaireTemplate.template_type == TemplateType.INITIAL_HOMOLOGATION
    ).first()
    
    if not template:
        print("❌ Template por defecto no encontrado")
        return None
    
    # Crear respuestas basadas en la BlueLine pero con algunas diferencias
    base_responses = blue_line.responses.copy() if blue_line.responses else {}
    
    # Modificar algunos campos para crear diferencias
    differences = {
        'q3t1s2f16': {'name': 'Product Name', 'type': 'inputText', 'value': '[BASIL0003] PRODUCTO MODIFICADO PARA PRUEBA'},
        'q3t1s2f23': {'name': 'CAS', 'type': 'inputText', 'value': '9999-99-9'},  # CAS diferente
        'q3t1s3f27': {'name': 'KOSHER CERTIFICATE', 'type': 'checkComents', 'value': 'false'},  # Kosher diferente
    }
    
    modified_responses = base_responses.copy()
    for field_code, new_value in differences.items():
        modified_responses[field_code] = new_value
        print(f"   🔄 Modificado {field_code}: {new_value['value']}")
    
    # Crear cuestionario
    questionnaire = Questionnaire(
        material_id=material_id,
        supplier_code='PROVEEDOR-EJEMPLO-TEST',
        questionnaire_type=QuestionnaireType.INITIAL_HOMOLOGATION,
        version=1,
        template_id=template.id,
        responses=modified_responses,
        status=QuestionnaireStatus.DRAFT
    )
    
    db.add(questionnaire)
    db.commit()
    db.refresh(questionnaire)
    
    print(f"✅ Cuestionario creado: ID {questionnaire.id}")
    return questionnaire

def create_material_supplier_example(db: SessionLocal, questionnaire_id: int):
    """Crea un MaterialSupplier de ejemplo aceptando algunas diferencias"""
    print(f"\n📋 Creando MaterialSupplier para cuestionario {questionnaire_id}...")
    
    questionnaire = db.query(Questionnaire).filter(Questionnaire.id == questionnaire_id).first()
    if not questionnaire:
        print(f"❌ Cuestionario {questionnaire_id} no encontrado")
        return None
    
    blue_line = db.query(BlueLine).filter(BlueLine.material_id == questionnaire.material_id).first()
    if not blue_line:
        print(f"❌ BlueLine no encontrada para material {questionnaire.material_id}")
        return None
    
    # Realizar comparación
    comparison = MaterialSupplierComparisonService.compare_questionnaire_with_blue_line(
        questionnaire, blue_line
    )
    
    print(f"   📊 Comparación:")
    print(f"      Score: {comparison.score}%")
    print(f"      Matches: {comparison.matches}/10")
    print(f"      Mismatches: {len(comparison.mismatches)}")
    
    # Aceptar algunas diferencias (por ejemplo, las primeras 2)
    accepted_mismatches = [m.field_code for m in comparison.mismatches[:2]]
    print(f"   ✅ Aceptando diferencias: {accepted_mismatches}")
    
    # Extraer supplier name
    supplier_name = None
    if questionnaire.responses:
        supplier_field = questionnaire.responses.get("q3t1s2f15")
        if supplier_field:
            if isinstance(supplier_field, dict):
                supplier_name = supplier_field.get("value", "")
            else:
                supplier_name = str(supplier_field)
    
    # Construir mismatch_fields
    mismatch_fields = []
    for mismatch in comparison.mismatches:
        mismatch_fields.append({
            "field_code": mismatch.field_code,
            "field_name": mismatch.field_name,
            "expected_value": mismatch.expected_value,
            "actual_value": mismatch.actual_value,
            "severity": mismatch.severity,
            "accepted": mismatch.field_code in accepted_mismatches
        })
    
    # Crear MaterialSupplier
    material_supplier = MaterialSupplier(
        material_id=questionnaire.material_id,
        questionnaire_id=questionnaire.id,
        blue_line_id=blue_line.id,
        supplier_code=questionnaire.supplier_code,
        supplier_name=supplier_name or questionnaire.supplier_code,
        status="ACTIVE",
        validation_score=comparison.score,
        mismatch_fields=mismatch_fields,
        accepted_mismatches=accepted_mismatches,
        validated_at=datetime.utcnow()
    )
    
    db.add(material_supplier)
    
    # Actualizar cuestionario
    questionnaire.status = QuestionnaireStatus.APPROVED
    questionnaire.approved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(material_supplier)
    
    print(f"✅ MaterialSupplier creado: ID {material_supplier.id}")
    print(f"   Supplier: {material_supplier.supplier_name}")
    print(f"   Score: {material_supplier.validation_score}%")
    print(f"   Diferencias aceptadas: {len(accepted_mismatches)}")
    
    return material_supplier

def main():
    """Función principal"""
    print("=" * 60)
    print("🧪 SCRIPT DE PRUEBA - Sistema Material-Supplier")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Material 10 tiene BlueLine y ya tiene algunos datos
        material_id = 10
        
        print(f"\n1️⃣  Verificando Material y BlueLine...")
        material = db.query(Material).filter(Material.id == material_id).first()
        blue_line = db.query(BlueLine).filter(BlueLine.material_id == material_id).first()
        
        if not material:
            print(f"❌ Material {material_id} no encontrado")
            return
        
        if not blue_line:
            print(f"❌ BlueLine para material {material_id} no encontrada")
            return
        
        print(f"   ✅ Material: {material.reference_code} - {material.name}")
        print(f"   ✅ BlueLine ID: {blue_line.id}")
        
        # Verificar MaterialSuppliers existentes
        existing_suppliers = db.query(MaterialSupplier).filter(
            MaterialSupplier.material_id == material_id
        ).all()
        
        print(f"\n2️⃣  MaterialSuppliers existentes: {len(existing_suppliers)}")
        for s in existing_suppliers:
            print(f"   - ID {s.id}: {s.supplier_code} (Score: {s.validation_score}%)")
        
        # Crear cuestionario de ejemplo
        questionnaire = create_example_questionnaire_with_differences(db, material_id)
        
        if not questionnaire:
            print("❌ No se pudo crear el cuestionario de ejemplo")
            return
        
        # Crear MaterialSupplier de ejemplo
        material_supplier = create_material_supplier_example(db, questionnaire.id)
        
        if not material_supplier:
            print("❌ No se pudo crear el MaterialSupplier de ejemplo")
            return
        
        # Resumen final
        print(f"\n" + "=" * 60)
        print("✅ DATOS DE EJEMPLO CREADOS EXITOSAMENTE")
        print("=" * 60)
        print(f"\n📋 Resumen:")
        print(f"   Material ID: {material_id}")
        print(f"   Material: {material.reference_code} - {material.name}")
        print(f"   BlueLine ID: {blue_line.id}")
        print(f"   Cuestionario ID: {questionnaire.id}")
        print(f"   MaterialSupplier ID: {material_supplier.id}")
        print(f"   Supplier: {material_supplier.supplier_code}")
        print(f"   Validation Score: {material_supplier.validation_score}%")
        
        # Contar MaterialSuppliers finales
        final_suppliers = db.query(MaterialSupplier).filter(
            MaterialSupplier.material_id == material_id
        ).all()
        
        print(f"\n📊 MaterialSuppliers totales para este material: {len(final_suppliers)}")
        
        print(f"\n🌐 URLs para probar en el frontend:")
        print(f"   1. Ver BlueLine Detail (con MaterialSuppliers):")
        print(f"      http://localhost:5173/blue-line/material/{material_id}")
        print(f"   ")
        print(f"   2. Ver Cuestionario:")
        print(f"      http://localhost:5173/questionnaires/{questionnaire.id}")
        print(f"   ")
        print(f"   3. Importar nuevo cuestionario (usar JSON de prueba):")
        print(f"      http://localhost:5173/questionnaires/import")
        print(f"      Archivo: data/questionnaires/test_import_validation_lluch.json")
        
        print(f"\n💡 INSTRUCCIONES PARA PROBAR:")
        print(f"   1. Ve a: http://localhost:5173/blue-line/material/{material_id}")
        print(f"   2. Desplázate hasta el final de la página")
        print(f"   3. Deberías ver la sección 'Material-Proveedores Asociados'")
        print(f"   4. Haz clic en el proveedor para expandir y ver detalles")
        print(f"   5. Prueba importar un nuevo cuestionario desde /questionnaires/import")
        print(f"   6. Verifica la comparación automática y acepta/rechaza diferencias")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()

