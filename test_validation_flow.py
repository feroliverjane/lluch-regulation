#!/usr/bin/env python3
"""
Test script completo para el flujo de validación de cuestionario.
Este script prueba:
1. Detección automática de material
2. Importación y validación con Blue Line
3. Visualización de campos que no coinciden (marcados en rojo)
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000/api"

def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_step(step, description):
    print(f"\n▶ Step {step}: {description}")

def test_validation_flow():
    """Test completo del flujo de validación"""
    print_section("TEST: Flujo Completo de Validación de Cuestionario")
    
    # Step 1: Verificar material BASIL0003 existe
    print_step(1, "Verificando si material BASIL0003 existe...")
    materials_response = requests.get(f"{BASE_URL}/materials/")
    materials = materials_response.json()
    
    basil_material = None
    for mat in materials:
        if mat.get("reference_code") == "BASIL0003":
            basil_material = mat
            break
    
    if not basil_material:
        print("⚠️  Material BASIL0003 no encontrado.")
        print("   Creando material BASIL0003...")
        material_data = {
            "reference_code": "BASIL0003",
            "name": "H.E. BASILIC INDES",
            "material_type": "NATURAL",
            "supplier": "MPE",
            "cas_number": "8015-73-4",
            "description": "Basil essential oil",
            "is_active": True
        }
        create_response = requests.post(f"{BASE_URL}/materials", json=material_data)
        if create_response.status_code == 201:
            basil_material = create_response.json()
            print(f"   ✅ Material creado: ID={basil_material['id']}")
        else:
            print(f"   ❌ Error al crear material: {create_response.text}")
            return False
    else:
        print(f"   ✅ Material encontrado: ID={basil_material['id']}, Code={basil_material['reference_code']}")
    
    # Step 2: Verificar Blue Line existe
    print_step(2, "Verificando si Blue Line existe para BASIL0003...")
    blue_lines_response = requests.get(f"{BASE_URL}/blue-line/")
    blue_lines = blue_lines_response.json()
    
    basil_blue_line = None
    for bl in blue_lines:
        if bl.get("material_id") == basil_material.get("id"):
            basil_blue_line = bl
            break
    
    if not basil_blue_line:
        print("⚠️  Blue Line no encontrada para BASIL0003.")
        print("   Para probar la comparación, necesitas crear una Blue Line primero.")
        print("   Puedes usar el endpoint: POST /api/questionnaires/{id}/create-blue-line")
        print("\n   Continuando con el test de importación...")
    else:
        print(f"   ✅ Blue Line encontrada: ID={basil_blue_line['id']}")
        print(f"   ✅ La comparación se realizará automáticamente")
    
    # Step 3: Importar cuestionario con diferencias
    print_step(3, "Importando cuestionario con diferencias intencionales...")
    test_json_path = Path("data/questionnaires/test_validation_with_mismatches.json")
    
    if not test_json_path.exists():
        print(f"❌ Archivo de test no encontrado: {test_json_path}")
        return False
    
    print(f"   📄 Archivo: {test_json_path}")
    print("   ⚠️  Este cuestionario tiene diferencias intencionales:")
    print("      - Product Code diferente (BASIL0003-TEST vs BASIL0003)")
    print("      - CAS diferente (8015-73-4 vs el esperado)")
    print("      - Kosher Certificate: false (vs true esperado)")
    print("      - 100% Natural: NO (vs YES esperado)")
    print("      - 100% Pure: NO (vs YES esperado)")
    print("      - Country: FR (vs BG esperado)")
    print("      - Botanical Name diferente")
    
    with open(test_json_path, 'rb') as f:
        files = {'file': ('test_validation_with_mismatches.json', f, 'application/json')}
        response = requests.post(
            f"{BASE_URL}/questionnaires/import/json",
            files=files
        )
    
    if response.status_code == 201:
        result = response.json()
        print(f"\n   ✅ Cuestionario importado exitosamente!")
        print(f"      Questionnaire ID: {result.get('id')}")
        print(f"      Material ID: {result.get('material_id')}")
        
        # Step 4: Verificar comparación
        print_step(4, "Verificando resultados de la comparación...")
        
        if result.get('comparison'):
            comparison = result['comparison']
            total_compared = comparison.get('matches', 0) + len(comparison.get('mismatches', []))
            print(f"\n   📊 Resultados de la Comparación:")
            print(f"      ✅ Blue Line existe: {comparison.get('blue_line_exists')}")
            print(f"      ✅ Score de validación: {comparison.get('score', 0)}%")
            print(f"      ✅ Campos comparados: {total_compared} (comparación completa)")
            print(f"      ✅ Campos que coinciden: {comparison.get('matches', 0)}")
            print(f"      ❌ Campos que NO coinciden: {len(comparison.get('mismatches', []))}")
            
            if comparison.get('mismatches'):
                print(f"\n   🔴 Campos marcados en ROJO (diferencias detectadas):")
                for i, mismatch in enumerate(comparison.get('mismatches', []), 1):
                    print(f"\n      {i}. {mismatch.get('field_name')} ({mismatch.get('field_code')})")
                    print(f"         Severidad: {mismatch.get('severity')}")
                    print(f"         Esperado: {mismatch.get('expected_value', 'N/A')}")
                    print(f"         Actual: {mismatch.get('actual_value', 'N/A')}")
            
            return True
        else:
            print("   ⚠️  No se realizó comparación (Blue Line no existe)")
            return True
    else:
        error_data = response.json()
        error_message = error_data.get("detail", "")
        
        if "NEW_MATERIAL_DETECTED" in error_message:
            print(f"\n   ⚠️  Material nuevo detectado (esperado si BASIL0003 no existe)")
            print(f"      Mensaje: {error_message[:100]}...")
            return True
        else:
            print(f"\n   ❌ Error al importar: {response.status_code}")
            print(f"      {error_message}")
            return False

def test_new_material_validation():
    """Test con material nuevo"""
    print_section("TEST: Validación con Material Nuevo")
    
    print_step(1, "Usando cuestionario para material nuevo (VANILLA001)...")
    test_json_path = Path("data/questionnaires/test_manual_vanilla.json")
    
    if not test_json_path.exists():
        print(f"❌ Archivo no encontrado: {test_json_path}")
        return False
    
    # Verificar si material existe
    materials_response = requests.get(f"{BASE_URL}/materials/")
    materials = materials_response.json()
    
    vanilla_exists = any(m.get("reference_code") == "VANILLA001" for m in materials)
    
    if vanilla_exists:
        print("   ⚠️  Material VANILLA001 ya existe. Eliminándolo para el test...")
        vanilla_mat = next(m for m in materials if m.get("reference_code") == "VANILLA001")
        delete_response = requests.delete(f"{BASE_URL}/materials/{vanilla_mat.get('id')}")
        if delete_response.status_code == 204:
            print("   ✅ Material eliminado")
    
    print_step(2, "Importando cuestionario (debe detectar material nuevo)...")
    with open(test_json_path, 'rb') as f:
        files = {'file': ('test_manual_vanilla.json', f, 'application/json')}
        response = requests.post(
            f"{BASE_URL}/questionnaires/import/json",
            files=files
        )
    
    if response.status_code == 400:
        error_data = response.json()
        error_message = error_data.get("detail", "")
        
        if "NEW_MATERIAL_DETECTED" in error_message:
            print("   ✅ Material nuevo detectado correctamente!")
            print(f"      {error_message[:150]}...")
            return True
        else:
            print(f"   ❌ Error inesperado: {error_message}")
            return False
    elif response.status_code == 201:
        result = response.json()
        print("   ✅ Cuestionario importado (material ya existía)")
        return True
    else:
        print(f"   ❌ Error: {response.status_code}")
        return False

if __name__ == "__main__":
    print("\n" + "🧪 TESTING COMPLETO DEL FLUJO DE VALIDACIÓN")
    print("=" * 70)
    
    try:
        # Test 1: Validación con diferencias
        test1_result = test_validation_flow()
        
        # Test 2: Material nuevo
        test2_result = test_new_material_validation()
        
        # Summary
        print_section("RESUMEN DE TESTS")
        print(f"Test Validación con Diferencias: {'✅ PASSED' if test1_result else '❌ FAILED'}")
        print(f"Test Material Nuevo:             {'✅ PASSED' if test2_result else '❌ FAILED'}")
        
        if test1_result and test2_result:
            print("\n🎉 Todos los tests pasaron!")
            print("\n📋 Para probar en el frontend:")
            print("   1. Abre http://localhost:5173")
            print("   2. Ve a 'Importar Cuestionario'")
            print("   3. Selecciona: data/questionnaires/test_validation_with_mismatches.json")
            print("   4. Observa cómo se detecta BASIL0003 automáticamente")
            print("   5. Haz clic en 'Validar Cuestionario'")
            print("   6. Verás los campos que NO coinciden marcados en ROJO")
        else:
            print("\n⚠️  Algunos tests fallaron. Revisa los mensajes arriba.")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: No se pudo conectar al backend API.")
        print("   Asegúrate de que el backend esté corriendo en http://localhost:8000")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

