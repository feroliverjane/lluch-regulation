#!/usr/bin/env python3
"""
Test script to verify all latest features work correctly:
1. Questionnaire import with automatic material detection
2. Comparison with Blue Line
3. Creating Blue Line from questionnaire
4. Creating Composite Z1
5. Viewing MaterialSuppliers
"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8000/api"

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_step(step, description):
    print(f"\n▶ Step {step}: {description}")

def test_questionnaire_import():
    """Test importing a questionnaire and automatic material detection"""
    print_section("TEST 1: Questionnaire Import with Auto Material Detection")
    
    # Check if material BASIL0003 exists
    print_step(1, "Checking if material BASIL0003 exists...")
    materials_response = requests.get(f"{BASE_URL}/materials/")
    materials = materials_response.json()
    
    basil_material = None
    for mat in materials:
        if mat.get("reference_code") == "BASIL0003":
            basil_material = mat
            break
    
    if not basil_material:
        print("⚠️  Material BASIL0003 not found. Creating it...")
        # Create material
        material_data = {
            "reference_code": "BASIL0003",
            "name": "H.E. BASILIC INDES",
            "supplier_code": "MPE",
            "category": "Essential Oil"
        }
        create_response = requests.post(f"{BASE_URL}/materials/", json=material_data)
        if create_response.status_code == 200:
            basil_material = create_response.json()
            print(f"✅ Material created: {basil_material['id']}")
        else:
            print(f"❌ Failed to create material: {create_response.text}")
            return None
    else:
        print(f"✅ Material found: ID={basil_material['id']}, Code={basil_material['reference_code']}")
    
    # Import questionnaire
    print_step(2, "Importing questionnaire from JSON file...")
    test_json_path = Path("data/questionnaires/test_import_validation_lluch.json")
    
    if not test_json_path.exists():
        print(f"❌ Test JSON file not found: {test_json_path}")
        return None
    
    with open(test_json_path, 'rb') as f:
        files = {'file': ('test_import_validation_lluch.json', f, 'application/json')}
        response = requests.post(
            f"{BASE_URL}/questionnaires/import/json",
            files=files
        )
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"✅ Questionnaire imported successfully!")
        print(f"   • Questionnaire ID: {result.get('id', 'N/A')}")
        print(f"   • Material ID: {result.get('material_id', 'N/A')}")
        print(f"   • Supplier Code: {result.get('supplier_code', 'N/A')}")
        
        # Check comparison result
        if 'comparison' in result and result['comparison']:
            comparison = result['comparison']
            print(f"\n📊 Comparison Results:")
            print(f"   • Blue Line Exists: {comparison.get('blue_line_exists', False)}")
            print(f"   • Validation Score: {comparison.get('score', 0)}%")
            print(f"   • Matches: {comparison.get('matches', 0)}")
            print(f"   • Mismatches: {len(comparison.get('mismatches', []))}")
            
            if comparison.get('mismatches'):
                print(f"\n   Mismatches found:")
                for mismatch in comparison['mismatches'][:5]:  # Show first 5
                    print(f"     - {mismatch.get('field_name', 'Unknown')}: "
                          f"{mismatch.get('expected_value', 'N/A')} vs "
                          f"{mismatch.get('actual_value', 'N/A')}")
        
        return result
    else:
        print(f"❌ Failed to import questionnaire: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def test_create_blue_line_from_questionnaire(questionnaire_id):
    """Test creating a Blue Line from a questionnaire"""
    print_section("TEST 2: Create Blue Line from Questionnaire")
    
    if not questionnaire_id:
        print("⚠️  No questionnaire ID provided. Skipping test.")
        return None
    
    print_step(1, f"Creating Blue Line from questionnaire {questionnaire_id}...")
    response = requests.post(f"{BASE_URL}/questionnaires/{questionnaire_id}/create-blue-line")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Blue Line created successfully!")
        print(f"   • Blue Line ID: {result['blue_line']['id']}")
        print(f"   • Material ID: {result['blue_line']['material_id']}")
        print(f"   • Material Supplier ID: {result.get('material_supplier', {}).get('id', 'N/A')}")
        return result
    else:
        print(f"❌ Failed to create Blue Line: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def test_create_composite(blue_line_id):
    """Test creating a Composite Z1 (mockup)"""
    print_section("TEST 3: Create Composite Z1 (Mockup)")
    
    if not blue_line_id:
        print("⚠️  No Blue Line ID provided. Skipping test.")
        return None
    
    print_step(1, f"Creating Composite Z1 for Blue Line {blue_line_id}...")
    response = requests.post(f"{BASE_URL}/blue-line/{blue_line_id}/create-composite")
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"✅ Composite Z1 created successfully!")
        if 'composite' in result:
            print(f"   • Composite ID: {result['composite'].get('id', result.get('composite_id', 'N/A'))}")
            print(f"   • Blue Line ID: {result['composite'].get('blue_line_id', result.get('blue_line_id', 'N/A'))}")
            print(f"   • Type: {result['composite'].get('composite_type', 'Z1')}")
        else:
            print(f"   • Composite ID: {result.get('composite_id', 'N/A')}")
            print(f"   • Blue Line ID: {result.get('blue_line_id', 'N/A')}")
            print(f"   • Message: {result.get('message', 'N/A')}")
        return result
    else:
        print(f"❌ Failed to create Composite: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def test_get_blue_line_detail(material_id):
    """Test getting Blue Line detail with MaterialSuppliers"""
    print_section("TEST 4: Get Blue Line Detail with MaterialSuppliers")
    
    if not material_id:
        print("⚠️  No material ID provided. Skipping test.")
        return None
    
    print_step(1, f"Fetching Blue Line detail for material {material_id}...")
    response = requests.get(f"{BASE_URL}/blue-line/material/{material_id}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Blue Line detail retrieved!")
        print(f"   • Blue Line ID: {result['id']}")
        print(f"   • Material ID: {result['material_id']}")
        print(f"   • Material Suppliers: {len(result.get('material_suppliers', []))}")
        
        if result.get('material_suppliers'):
            print(f"\n   Material Suppliers:")
            for ms in result['material_suppliers']:
                print(f"     - Supplier: {ms.get('supplier_name', 'N/A')} ({ms.get('supplier_code', 'N/A')})")
                print(f"       Validation Score: {ms.get('validation_score', 0)}%")
                print(f"       Status: {ms.get('status', 'N/A')}")
                print(f"       Mismatches: {len(ms.get('mismatch_fields', []))}")
        return result
    else:
        print(f"❌ Failed to get Blue Line detail: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def test_material_suppliers_list(material_id=None):
    """Test getting list of MaterialSuppliers"""
    print_section("TEST 5: List MaterialSuppliers")
    
    if material_id:
        print_step(1, f"Fetching MaterialSuppliers for material {material_id}...")
        response = requests.get(f"{BASE_URL}/material-suppliers/by-material/{material_id}")
    else:
        print_step(1, "Material ID not provided. Skipping MaterialSuppliers list test.")
        return None
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Found {len(result)} MaterialSupplier records")
        
        for ms in result[:5]:  # Show first 5
            print(f"\n   • ID: {ms['id']}")
            print(f"     Supplier: {ms.get('supplier_name', 'N/A')} ({ms.get('supplier_code', 'N/A')})")
            print(f"     Validation Score: {ms.get('validation_score', 0)}%")
            print(f"     Blue Line ID: {ms.get('blue_line_id', 'N/A')}")
            print(f"     Status: {ms.get('status', 'N/A')}")
        return result
    else:
        print(f"❌ Failed to get MaterialSuppliers: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def main():
    """Run all tests"""
    print("\n" + "🚀"*40)
    print("  COMPREHENSIVE FEATURE TEST")
    print("🚀"*40)
    
    # Wait for backend to be ready
    print("\n⏳ Waiting for backend to be ready...")
    for i in range(10):
        try:
            response = requests.get(f"{BASE_URL}/materials/", timeout=2)
            if response.status_code == 200:
                print("✅ Backend is ready!")
                break
        except:
            pass
        time.sleep(1)
        if i == 9:
            print("❌ Backend not responding. Please ensure it's running on port 8000.")
            return
    
    # Run tests
    questionnaire_result = test_questionnaire_import()
    
    questionnaire_id = None
    material_id = None
    blue_line_id = None
    
    if questionnaire_result:
        questionnaire_id = questionnaire_result.get('id')
        material_id = questionnaire_result.get('material_id')
        
        # Test creating Blue Line if it doesn't exist
        comparison = questionnaire_result.get('comparison', {}) or {}
        if not comparison.get('blue_line_exists', False):
            blue_line_result = test_create_blue_line_from_questionnaire(questionnaire_id)
            if blue_line_result:
                blue_line_id = blue_line_result['blue_line']['id']
        else:
            print("\n⚠️  Blue Line already exists. Skipping creation test.")
            # Try to get existing Blue Line
            bl_response = requests.get(f"{BASE_URL}/blue-line/material/{material_id}")
            if bl_response.status_code == 200:
                blue_line_id = bl_response.json()['id']
        
        # Test creating Composite
        if blue_line_id:
            test_create_composite(blue_line_id)
        
        # Test getting Blue Line detail
        if material_id:
            test_get_blue_line_detail(material_id)
    
    # Test listing MaterialSuppliers
    test_material_suppliers_list(material_id)
    
    print_section("TEST SUMMARY")
    print("✅ All tests completed!")
    print("\n📝 Next steps:")
    print("   1. Check the frontend at http://localhost:5173")
    print("   2. Navigate to Questionnaire Import page")
    print("   3. Upload the test JSON file")
    print("   4. Verify comparison results are displayed")
    print("   5. Check Blue Line Detail page for MaterialSuppliers")

if __name__ == "__main__":
    main()

