#!/usr/bin/env python3
"""
Test script to verify new material detection when importing a questionnaire JSON.
This script tests that when a JSON contains a material code that doesn't exist,
the system correctly detects it as a new material and shows an appropriate message.
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

def test_new_material_detection():
    """Test that new material detection works correctly"""
    print_section("TEST: New Material Detection on Questionnaire Import")
    
    # Step 1: Check if material ROSE0001 exists
    print_step(1, "Checking if material ROSE0001 exists...")
    materials_response = requests.get(f"{BASE_URL}/materials/")
    materials = materials_response.json()
    
    rose_material = None
    for mat in materials:
        if mat.get("reference_code") == "ROSE0001":
            rose_material = mat
            break
    
    if rose_material:
        print(f"⚠️  Material ROSE0001 already exists (ID: {rose_material['id']})")
        print("   This test requires the material to NOT exist.")
        print("   Please delete the material first or use a different material code.")
        return False
    else:
        print("✅ Material ROSE0001 does not exist - perfect for testing!")
    
    # Step 2: Try to import questionnaire for non-existent material
    print_step(2, "Importing questionnaire JSON for non-existent material ROSE0001...")
    test_json_path = Path("data/questionnaires/ejemplo_cuestionario_nuevo_material.json")
    
    if not test_json_path.exists():
        print(f"❌ Test JSON file not found: {test_json_path}")
        return False
    
    print(f"   Using JSON file: {test_json_path}")
    
    # Read JSON to verify it contains ROSE0001
    with open(test_json_path, 'r') as f:
        json_data = json.load(f)
        product_name_field = None
        for item in json_data.get("data", []):
            if item.get("fieldCode") == "q3t1s2f16":  # Product Name
                product_name_field = item.get("value", "")
                break
        
        if product_name_field and "ROSE0001" in product_name_field:
            print(f"   ✅ JSON contains material code ROSE0001 in Product Name: {product_name_field}")
        else:
            print(f"   ⚠️  Could not verify material code in JSON")
    
    # Try to import without specifying material (let backend detect from JSON)
    print_step(3, "Attempting import without specifying material (auto-detect from JSON)...")
    
    with open(test_json_path, 'rb') as f:
        files = {'file': ('ejemplo_cuestionario_nuevo_material.json', f, 'application/json')}
        response = requests.post(
            f"{BASE_URL}/questionnaires/import/json",
            files=files
        )
    
    print(f"   Response status: {response.status_code}")
    
    if response.status_code == 400:
        error_data = response.json()
        error_message = error_data.get("detail", "")
        
        print(f"   ✅ Expected error received (400 Bad Request)")
        print(f"   Error message: {error_message}")
        
        if "NEW_MATERIAL_DETECTED" in error_message:
            print("\n   ✅✅✅ SUCCESS! New material detection is working correctly!")
            print(f"   ✅ Error message correctly identifies this as a new material")
            
            # Extract material code from error message
            if "ROSE0001" in error_message:
                print(f"   ✅ Material code ROSE0001 correctly extracted from JSON")
            
            return True
        else:
            print("\n   ❌ ERROR: Error message does not indicate new material detection")
            print(f"   Expected: 'NEW_MATERIAL_DETECTED' in error message")
            print(f"   Actual: {error_message}")
            return False
    else:
        print(f"\n   ❌ Unexpected response status: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def test_existing_material_import():
    """Test that import works correctly for existing material"""
    print_section("TEST: Import with Existing Material (for comparison)")
    
    # Find any existing material
    print_step(1, "Finding an existing material...")
    materials_response = requests.get(f"{BASE_URL}/materials/")
    materials = materials_response.json()
    
    if not materials:
        print("   ⚠️  No materials found. Skipping this test.")
        return True
    
    existing_material = materials[0]
    print(f"   ✅ Found material: {existing_material['reference_code']} (ID: {existing_material['id']})")
    
    # Create a simple test JSON with this material code
    print_step(2, "Creating test JSON with existing material code...")
    test_json = {
        "requestId": 9999,
        "data": [
            {
                "fieldCode": "q3t1s2f15",
                "fieldName": "Supplier Name",
                "fieldType": "inputText",
                "value": "TEST SUPPLIER"
            },
            {
                "fieldCode": "q3t1s2f16",
                "fieldName": "Product Name",
                "fieldType": "inputText",
                "value": f"[{existing_material['reference_code']}] Test Product"
            },
            {
                "fieldCode": "q3t1s2f17",
                "fieldName": "Supplier´s product code",
                "fieldType": "inputText",
                "value": existing_material['reference_code']
            }
        ]
    }
    
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_json, f)
        temp_path = Path(f.name)
    
    print_step(3, "Importing questionnaire for existing material...")
    with open(temp_path, 'rb') as f:
        files = {'file': ('test_existing_material.json', f, 'application/json')}
        response = requests.post(
            f"{BASE_URL}/questionnaires/import/json",
            files=files
        )
    
    # Clean up temp file
    temp_path.unlink()
    
    if response.status_code == 201:
        result = response.json()
        print(f"   ✅ Import successful! Questionnaire ID: {result.get('id')}")
        print(f"   ✅ Material ID: {result.get('material_id')}")
        print(f"   ✅ Comparison result: {'Available' if result.get('comparison') else 'Not available'}")
        return True
    else:
        print(f"   ⚠️  Import failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

if __name__ == "__main__":
    print("\n" + "🧪 TESTING NEW MATERIAL DETECTION FEATURE")
    print("=" * 70)
    
    try:
        # Test 1: New material detection
        test1_result = test_new_material_detection()
        
        # Test 2: Existing material import (for comparison)
        test2_result = test_existing_material_import()
        
        # Summary
        print_section("TEST SUMMARY")
        print(f"New Material Detection Test: {'✅ PASSED' if test1_result else '❌ FAILED'}")
        print(f"Existing Material Import Test: {'✅ PASSED' if test2_result else '❌ FAILED'}")
        
        if test1_result and test2_result:
            print("\n🎉 All tests passed!")
        else:
            print("\n⚠️  Some tests failed. Please review the output above.")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to backend API.")
        print("   Make sure the backend is running on http://localhost:8000")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()














