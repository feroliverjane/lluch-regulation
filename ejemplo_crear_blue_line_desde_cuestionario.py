#!/usr/bin/env python3
"""
Ejemplo completo para crear una Blue Line desde cero usando un cuestionario.

Este script demuestra el flujo completo:
1. Crear un material nuevo
2. Importar un cuestionario JSON (formato Lluch)
3. Crear la Blue Line desde el cuestionario
4. Opcionalmente crear el Composite Z1 mockup

Uso:
    python ejemplo_crear_blue_line_desde_cuestionario.py
"""

import requests
import json
from pathlib import Path
from typing import Optional

# Configuración
API_BASE_URL = "http://localhost:8000/api"

def print_section(title: str):
    """Imprime un separador visual"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_step(step: int, description: str):
    """Imprime un paso del proceso"""
    print(f"\n▶ Paso {step}: {description}")

def create_material(reference_code: str, name: str, supplier_code: str = "PROVEEDOR-TEST") -> Optional[dict]:
    """Crea un nuevo material"""
    print_step(1, f"Creando material: {reference_code}")
    
    material_data = {
        "reference_code": reference_code,
        "name": name,
        "supplier_code": supplier_code,
        "category": "Essential Oil",
        "cas_number": "000-00-0",  # Se actualizará desde el cuestionario
        "is_active": True
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/materials/", json=material_data)
        if response.status_code in [200, 201]:
            material = response.json()
            print(f"   ✅ Material creado exitosamente")
            print(f"      • ID: {material['id']}")
            print(f"      • Código: {material['reference_code']}")
            print(f"      • Nombre: {material['name']}")
            return material
        else:
            # Puede que el material ya exista
            if response.status_code == 400:
                print(f"   ⚠️  El material ya existe, buscando...")
                # Buscar el material existente
                search_response = requests.get(f"{API_BASE_URL}/materials/")
                if search_response.status_code == 200:
                    materials = search_response.json()
                    for mat in materials:
                        if mat.get("reference_code") == reference_code:
                            print(f"   ✅ Material encontrado: ID={mat['id']}")
                            return mat
            print(f"   ❌ Error al crear material: {response.status_code}")
            print(f"      {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def import_questionnaire(json_file_path: str, material_id: int) -> Optional[dict]:
    """Importa un cuestionario desde un archivo JSON"""
    print_step(2, f"Importando cuestionario desde: {json_file_path}")
    
    file_path = Path(json_file_path)
    if not file_path.exists():
        print(f"   ❌ Archivo no encontrado: {json_file_path}")
        return None
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'application/json')}
            data = {'material_id': material_id}
            
            response = requests.post(
                f"{API_BASE_URL}/questionnaires/import/json",
                files=files,
                data=data
            )
        
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"   ✅ Cuestionario importado exitosamente")
            print(f"      • Questionnaire ID: {result['id']}")
            print(f"      • Material ID: {result['material_id']}")
            print(f"      • Supplier Code: {result['supplier_code']}")
            
            # Mostrar resultados de comparación si existen
            if result.get('comparison'):
                comparison = result['comparison']
                print(f"\n   📊 Resultados de Comparación:")
                print(f"      • Blue Line Existe: {comparison.get('blue_line_exists', False)}")
                print(f"      • Score: {comparison.get('score', 0)}%")
                print(f"      • Matches: {comparison.get('matches', 0)}")
                print(f"      • Mismatches: {len(comparison.get('mismatches', []))}")
                
                if not comparison.get('blue_line_exists'):
                    print(f"\n   💡 No existe Blue Line para este material. Puedes crearla ahora.")
            
            return result
        else:
            print(f"   ❌ Error al importar cuestionario: {response.status_code}")
            print(f"      {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def create_blue_line_from_questionnaire(questionnaire_id: int, create_composite: bool = False) -> Optional[dict]:
    """Crea una Blue Line desde un cuestionario"""
    print_step(3, f"Creando Blue Line desde cuestionario {questionnaire_id}")
    
    try:
        url = f"{API_BASE_URL}/questionnaires/{questionnaire_id}/create-blue-line"
        params = {"create_composite": "false"}  # El composite vacío se crea automáticamente
        
        response = requests.post(url, params=params)
        
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"   ✅ Blue Line creada exitosamente")
            print(f"      • Blue Line ID: {result.get('blue_line', {}).get('id', result.get('blue_line_id', 'N/A'))}")
            print(f"      • Material ID: {result.get('blue_line', {}).get('material_id', result.get('material_id', 'N/A'))}")
            print(f"      • Composite ID: {result.get('blue_line', {}).get('composite_id', result.get('composite_id', 'N/A'))}")
            print(f"      • Material Supplier ID: {result.get('material_supplier', {}).get('id', 'N/A')}")
            
            blue_line_id = result.get('blue_line', {}).get('id') or result.get('blue_line_id')
            composite_id = result.get('blue_line', {}).get('composite_id') or result.get('composite_id')
            
            return {
                'blue_line_id': blue_line_id,
                'composite_id': composite_id,
                'full_result': result
            }
        else:
            print(f"   ❌ Error al crear Blue Line: {response.status_code}")
            print(f"      {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def create_composite_z1_mockup(blue_line_id: int) -> Optional[dict]:
    """Crea un Composite Z1 mockup para una Blue Line"""
    print_step(4, f"Creando Composite Z1 mockup para Blue Line {blue_line_id}")
    
    try:
        response = requests.post(f"{API_BASE_URL}/blue-line/{blue_line_id}/create-composite")
        
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"   ✅ Composite Z1 creado exitosamente")
            print(f"      • Composite ID: {result.get('composite', {}).get('id', result.get('composite_id', 'N/A'))}")
            print(f"      • Blue Line ID: {result.get('blue_line_id', 'N/A')}")
            print(f"      • Componentes: {result.get('components_count', 0)}")
            print(f"      • Mensaje: {result.get('message', 'N/A')}")
            return result
        else:
            print(f"   ❌ Error al crear Composite: {response.status_code}")
            print(f"      {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def get_blue_line_detail(material_id: int) -> Optional[dict]:
    """Obtiene los detalles de una Blue Line por material_id"""
    print_step(5, f"Obteniendo detalles de Blue Line para material {material_id}")
    
    try:
        response = requests.get(f"{API_BASE_URL}/blue-line/material/{material_id}")
        
        if response.status_code == 200:
            blue_line = response.json()
            print(f"   ✅ Blue Line encontrada")
            print(f"      • Blue Line ID: {blue_line['id']}")
            print(f"      • Material ID: {blue_line['material_id']}")
            print(f"      • Tipo: {blue_line.get('material_type', 'N/A')}")
            print(f"      • Composite ID: {blue_line.get('composite_id', 'N/A')}")
            print(f"      • Campos definidos: {len(blue_line.get('responses', {}))}")
            return blue_line
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"      {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def main():
    """Función principal que ejecuta el ejemplo completo"""
    print("\n" + "🚀"*40)
    print("  EJEMPLO: Crear Blue Line desde Cuestionario")
    print("🚀"*40)
    
    # Verificar que el backend esté disponible
    try:
        response = requests.get(f"{API_BASE_URL.replace('/api', '/health')}", timeout=2)
        if response.status_code != 200:
            print("\n❌ Backend no disponible. Asegúrate de que esté corriendo en http://localhost:8000")
            return
    except:
        print("\n❌ No se puede conectar al backend. Asegúrate de que esté corriendo en http://localhost:8000")
        return
    
    print("\n✅ Backend disponible")
    
    # ========== CONFIGURACIÓN ==========
    # Puedes cambiar estos valores según tus necesidades
    MATERIAL_CODE = "ROSE0001"  # Código único del material
    MATERIAL_NAME = "Rose Essential Oil"  # Nombre del material
    SUPPLIER_CODE = "PROVEEDOR-EJEMPLO"
    JSON_FILE = "data/questionnaires/test_import_validation_lluch.json"  # Archivo JSON del cuestionario
    
    # Si quieres usar un material existente, cambia esto a True
    USE_EXISTING_MATERIAL = False
    
    print_section("CONFIGURACIÓN")
    print(f"Material Code: {MATERIAL_CODE}")
    print(f"Material Name: {MATERIAL_NAME}")
    print(f"Supplier Code: {SUPPLIER_CODE}")
    print(f"JSON File: {JSON_FILE}")
    print(f"Usar material existente: {USE_EXISTING_MATERIAL}")
    
    # ========== PASO 1: Crear o obtener Material ==========
    print_section("PASO 1: Material")
    
    if USE_EXISTING_MATERIAL:
        # Buscar material existente
        response = requests.get(f"{API_BASE_URL}/materials/")
        if response.status_code == 200:
            materials = response.json()
            material = next((m for m in materials if m.get("reference_code") == MATERIAL_CODE), None)
            if material:
                print(f"✅ Material encontrado: ID={material['id']}")
            else:
                print(f"❌ Material {MATERIAL_CODE} no encontrado")
                return
        else:
            print(f"❌ Error al buscar materiales")
            return
    else:
        material = create_material(MATERIAL_CODE, MATERIAL_NAME, SUPPLIER_CODE)
        if not material:
            print("\n❌ No se pudo crear/obtener el material. Abortando.")
            return
    
    material_id = material['id']
    
    # ========== PASO 2: Importar Cuestionario ==========
    print_section("PASO 2: Importar Cuestionario")
    
    # Modificar el JSON para que apunte al material correcto
    # Leer el JSON original
    json_path = Path(JSON_FILE)
    if not json_path.exists():
        print(f"\n❌ Archivo JSON no encontrado: {JSON_FILE}")
        print(f"   Por favor, asegúrate de que el archivo existe.")
        return
    
    questionnaire_result = import_questionnaire(str(json_path), material_id)
    
    if not questionnaire_result:
        print("\n❌ No se pudo importar el cuestionario. Abortando.")
        return
    
    questionnaire_id = questionnaire_result['id']
    
    # Verificar si ya existe Blue Line
    comparison = questionnaire_result.get('comparison', {})
    if comparison.get('blue_line_exists'):
        print(f"\n⚠️  Ya existe una Blue Line para este material.")
        print(f"   Si quieres crear una nueva, primero elimina la existente.")
        return
    
    # ========== PASO 3: Crear Blue Line ==========
    print_section("PASO 3: Crear Blue Line desde Cuestionario")
    
    blue_line_result = create_blue_line_from_questionnaire(questionnaire_id, create_composite=False)
    
    if not blue_line_result:
        print("\n❌ No se pudo crear la Blue Line. Abortando.")
        return
    
    blue_line_id = blue_line_result['blue_line_id']
    composite_id = blue_line_result['composite_id']
    
    # ========== PASO 4 (Opcional): Crear Composite Z1 Mockup ==========
    print_section("PASO 4 (Opcional): Crear Composite Z1 Mockup")
    
    respuesta = input("\n¿Quieres crear un Composite Z1 mockup? (s/n): ").strip().lower()
    if respuesta == 's':
        composite_result = create_composite_z1_mockup(blue_line_id)
        if composite_result:
            print(f"\n✅ Composite Z1 mockup creado con éxito")
    
    # ========== PASO 5: Verificar Blue Line Creada ==========
    print_section("PASO 5: Verificar Blue Line")
    
    blue_line_detail = get_blue_line_detail(material_id)
    
    if blue_line_detail:
        print(f"\n✅ Blue Line verificada correctamente")
    
    # ========== RESUMEN ==========
    print_section("RESUMEN")
    print(f"✅ Proceso completado exitosamente!")
    print(f"\n📋 Resumen de lo creado:")
    print(f"   • Material ID: {material_id}")
    print(f"   • Material Code: {MATERIAL_CODE}")
    print(f"   • Questionnaire ID: {questionnaire_id}")
    print(f"   • Blue Line ID: {blue_line_id}")
    print(f"   • Composite ID: {composite_id}")
    
    print(f"\n🔗 URLs útiles:")
    print(f"   • Material Detail: http://localhost:5173/materials/{material_id}")
    print(f"   • Blue Line Detail: http://localhost:5173/blue-line/material/{material_id}")
    print(f"   • Questionnaire Detail: http://localhost:5173/questionnaires/{questionnaire_id}")
    if composite_id:
        print(f"   • Composite Detail: http://localhost:5173/composites/{composite_id}")
    
    print(f"\n💡 Notas:")
    print(f"   • La Blue Line fue creada con los valores del cuestionario")
    print(f"   • Se creó un Composite vacío automáticamente")
    print(f"   • Puedes editar el Composite manualmente o crear un Z1 mockup")
    print(f"   • La Blue Line está lista para ser comparada con futuros cuestionarios")

if __name__ == "__main__":
    main()

