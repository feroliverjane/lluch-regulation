#!/usr/bin/env python3
"""
Script para borrar materiales de prueba de la base de datos.
"""

import requests
import sys

BASE_URL = "http://localhost:8000/api"

def delete_material(reference_code):
    """Delete a material by reference code"""
    print(f"\n🔍 Buscando material con código: {reference_code}")
    
    # Get all materials
    response = requests.get(f"{BASE_URL}/materials/")
    if response.status_code != 200:
        print(f"❌ Error al obtener materiales: {response.status_code}")
        return False
    
    materials = response.json()
    
    # Find material
    material = None
    for mat in materials:
        if mat.get("reference_code") == reference_code:
            material = mat
            break
    
    if not material:
        print(f"⚠️  Material '{reference_code}' no encontrado en la base de datos")
        return False
    
    print(f"✅ Material encontrado:")
    print(f"   ID: {material.get('id')}")
    print(f"   Código: {material.get('reference_code')}")
    print(f"   Nombre: {material.get('name')}")
    
    # Delete material
    print(f"\n🗑️  Eliminando material...")
    delete_response = requests.delete(f"{BASE_URL}/materials/{material.get('id')}")
    
    if delete_response.status_code == 204:
        print(f"✅ Material '{reference_code}' eliminado exitosamente")
        return True
    else:
        print(f"❌ Error al eliminar material: {delete_response.status_code}")
        print(f"   Response: {delete_response.text}")
        return False

def list_test_materials():
    """List all test materials"""
    print("\n📋 Materiales de prueba en la base de datos:")
    print("=" * 70)
    
    response = requests.get(f"{BASE_URL}/materials/")
    if response.status_code != 200:
        print(f"❌ Error al obtener materiales: {response.status_code}")
        return
    
    materials = response.json()
    test_materials = ['JASMINE001', 'VANILLA001', 'ROSE0001']
    
    found = False
    for mat in materials:
        code = mat.get("reference_code", "")
        if code in test_materials:
            found = True
            print(f"   • {code} - {mat.get('name')} (ID: {mat.get('id')})")
    
    if not found:
        print("   ⚠️  No se encontraron materiales de prueba")

if __name__ == "__main__":
    print("\n" + "🧹 LIMPIEZA DE MATERIALES DE PRUEBA")
    print("=" * 70)
    
    if len(sys.argv) > 1:
        # Delete specific material
        code = sys.argv[1].upper()
        delete_material(code)
    else:
        # Interactive mode
        print("\n¿Qué material quieres eliminar?")
        print("   1. JASMINE001")
        print("   2. VANILLA001")
        print("   3. ROSE0001")
        print("   4. Listar todos los materiales de prueba")
        print("   5. Eliminar todos los materiales de prueba")
        
        choice = input("\nElige una opción (1-5): ").strip()
        
        if choice == "1":
            delete_material("JASMINE001")
        elif choice == "2":
            delete_material("VANILLA001")
        elif choice == "3":
            delete_material("ROSE0001")
        elif choice == "4":
            list_test_materials()
        elif choice == "5":
            print("\n🗑️  Eliminando todos los materiales de prueba...")
            for code in ["JASMINE001", "VANILLA001", "ROSE0001"]:
                delete_material(code)
        else:
            print("❌ Opción no válida")
    
    print("\n✅ Proceso completado")




