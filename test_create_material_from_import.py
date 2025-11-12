#!/usr/bin/env python3
"""
Test script to verify material creation from questionnaire import flow.
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000/api"

def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_material_creation():
    """Test creating a material via API"""
    print_section("TEST: Material Creation via API")
    
    # Check if material exists
    print("\nStep 1: Checking if material JASMINE001 exists...")
    materials_response = requests.get(f"{BASE_URL}/materials/")
    materials = materials_response.json()
    
    jasmine_material = None
    for mat in materials:
        if mat.get("reference_code") == "JASMINE001":
            jasmine_material = mat
            break
    
    if jasmine_material:
        print(f"⚠️  Material JASMINE001 already exists (ID: {jasmine_material['id']})")
        print("   Deleting it for testing...")
        delete_response = requests.delete(f"{BASE_URL}/materials/{jasmine_material['id']}")
        if delete_response.status_code == 204:
            print("   ✅ Material deleted")
        else:
            print(f"   ⚠️  Could not delete: {delete_response.status_code}")
    else:
        print("✅ Material JASMINE001 does not exist - perfect for testing!")
    
    # Create material
    print("\nStep 2: Creating material JASMINE001...")
    material_data = {
        "reference_code": "JASMINE001",
        "name": "Jasmine Essential Oil",
        "material_type": "NATURAL",
        "supplier": "PROVEEDOR TEST MANUAL",
        "cas_number": "8024-08-6",
        "description": "Material creado automáticamente desde cuestionario importado",
        "is_active": True
    }
    
    create_response = requests.post(f"{BASE_URL}/materials", json=material_data)
    
    if create_response.status_code == 201:
        created_material = create_response.json()
        print(f"✅ Material created successfully!")
        print(f"   ID: {created_material.get('id')}")
        print(f"   Code: {created_material.get('reference_code')}")
        print(f"   Name: {created_material.get('name')}")
        return True
    else:
        print(f"❌ Failed to create material: {create_response.status_code}")
        print(f"   Response: {create_response.text}")
        return False

def test_import_after_material_creation():
    """Test importing questionnaire after material is created"""
    print_section("TEST: Import Questionnaire After Material Creation")
    
    test_json_path = Path("data/questionnaires/test_manual_jasmine.json")
    
    print("\nStep 1: Importing questionnaire for existing material...")
    with open(test_json_path, 'rb') as f:
        files = {'file': ('test_manual_jasmine.json', f, 'application/json')}
        response = requests.post(
            f"{BASE_URL}/questionnaires/import/json",
            files=files
        )
    
    if response.status_code == 201:
        result = response.json()
        print(f"✅ Import successful!")
        print(f"   Questionnaire ID: {result.get('id')}")
        print(f"   Material ID: {result.get('material_id')}")
        print(f"   Comparison available: {'Yes' if result.get('comparison') else 'No'}")
        return True
    else:
        print(f"❌ Import failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

if __name__ == "__main__":
    print("\n" + "🧪 TESTING MATERIAL CREATION FROM IMPORT")
    print("=" * 70)
    
    try:
        # Test 1: Create material
        test1_result = test_material_creation()
        
        # Test 2: Import after creation
        test2_result = test_import_after_material_creation()
        
        # Summary
        print_section("TEST SUMMARY")
        print(f"Material Creation: {'✅ PASSED' if test1_result else '❌ FAILED'}")
        print(f"Import After Creation: {'✅ PASSED' if test2_result else '❌ FAILED'}")
        
        if test1_result and test2_result:
            print("\n🎉 All tests passed!")
        else:
            print("\n⚠️  Some tests failed.")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to backend API.")
        print("   Make sure the backend is running on http://localhost:8000")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()













