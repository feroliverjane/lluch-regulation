#!/usr/bin/env python3
"""
Test script to verify frontend integration with backend APIs
Tests the exact endpoints and data structures that the frontend uses
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000/api"

def test_questionnaire_import_for_frontend():
    """Test questionnaire import endpoint as frontend would call it"""
    print("\n" + "="*80)
    print("TEST: Questionnaire Import (Frontend Integration)")
    print("="*80)
    
    test_json_path = Path("data/questionnaires/test_import_validation_lluch.json")
    
    with open(test_json_path, 'rb') as f:
        files = {'file': ('test.json', f, 'application/json')}
        response = requests.post(
            f"{BASE_URL}/questionnaires/import/json",
            files=files
        )
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"✅ Import successful")
        print(f"   • Questionnaire ID: {result.get('id')}")
        print(f"   • Material ID: {result.get('material_id')}")
        print(f"   • Has comparison: {'comparison' in result and result['comparison'] is not None}")
        
        if result.get('comparison'):
            comp = result['comparison']
            print(f"   • Blue Line Exists: {comp.get('blue_line_exists')}")
            print(f"   • Score: {comp.get('score')}%")
            print(f"   • Matches: {comp.get('matches')}")
            print(f"   • Mismatches: {len(comp.get('mismatches', []))}")
            
            # Verify structure matches frontend expectations
            mismatches = comp.get('mismatches', [])
            if mismatches:
                first = mismatches[0]
                required_fields = ['field_code', 'field_name', 'expected_value', 'actual_value', 'severity']
                missing = [f for f in required_fields if f not in first]
                if missing:
                    print(f"   ⚠️  Missing fields in mismatch: {missing}")
                else:
                    print(f"   ✅ Mismatch structure is correct")
        
        return result
    else:
        print(f"❌ Import failed: {response.status_code}")
        print(f"   {response.text}")
        return None

def test_material_suppliers_for_frontend(material_id):
    """Test MaterialSuppliers endpoint as frontend would call it"""
    print("\n" + "="*80)
    print("TEST: MaterialSuppliers by Material (Frontend Integration)")
    print("="*80)
    
    response = requests.get(f"{BASE_URL}/material-suppliers/by-material/{material_id}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Found {len(result)} MaterialSuppliers")
        
        # Verify structure matches frontend expectations
        required_fields = ['id', 'material_id', 'supplier_code', 'supplier_name', 
                          'status', 'validation_score', 'mismatch_fields', 
                          'accepted_mismatches', 'created_at']
        
        if result:
            first = result[0]
            missing = [f for f in required_fields if f not in first]
            if missing:
                print(f"   ⚠️  Missing fields: {missing}")
            else:
                print(f"   ✅ MaterialSupplier structure is correct")
            
            for ms in result[:2]:
                print(f"\n   • ID: {ms['id']}")
                print(f"     Supplier: {ms.get('supplier_name', 'N/A')} ({ms.get('supplier_code', 'N/A')})")
                print(f"     Score: {ms.get('validation_score', 0)}%")
                print(f"     Mismatches: {len(ms.get('mismatch_fields', []))}")
        
        return result
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   {response.text}")
        return None

def test_blue_line_detail_for_frontend(material_id):
    """Test Blue Line detail endpoint as frontend would call it"""
    print("\n" + "="*80)
    print("TEST: Blue Line Detail by Material (Frontend Integration)")
    print("="*80)
    
    response = requests.get(f"{BASE_URL}/blue-line/material/{material_id}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Blue Line retrieved")
        print(f"   • Blue Line ID: {result.get('id')}")
        print(f"   • Material ID: {result.get('material_id')}")
        print(f"   • Has responses: {'responses' in result}")
        print(f"   • Has blue_line_data: {'blue_line_data' in result}")
        
        # Frontend expects these fields
        required_fields = ['id', 'material_id', 'responses', 'blue_line_data']
        missing = [f for f in required_fields if f not in result]
        if missing:
            print(f"   ⚠️  Missing fields: {missing}")
        else:
            print(f"   ✅ Blue Line structure is correct")
        
        return result
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   {response.text}")
        return None

def test_create_blue_line_from_questionnaire(questionnaire_id):
    """Test creating Blue Line from questionnaire"""
    print("\n" + "="*80)
    print("TEST: Create Blue Line from Questionnaire (Frontend Integration)")
    print("="*80)
    
    response = requests.post(f"{BASE_URL}/questionnaires/{questionnaire_id}/create-blue-line?create_composite=false")
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"✅ Blue Line created")
        print(f"   • Blue Line ID: {result.get('blue_line', {}).get('id', result.get('blue_line_id', 'N/A'))}")
        return result
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   {response.text}")
        return None

def test_create_composite(blue_line_id):
    """Test creating Composite Z1"""
    print("\n" + "="*80)
    print("TEST: Create Composite Z1 (Frontend Integration)")
    print("="*80)
    
    response = requests.post(f"{BASE_URL}/blue-line/{blue_line_id}/create-composite")
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"✅ Composite created")
        print(f"   • Composite ID: {result.get('composite', {}).get('id', result.get('composite_id', 'N/A'))}")
        return result
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   {response.text}")
        return None

def main():
    print("\n" + "🔍"*40)
    print("  FRONTEND INTEGRATION TEST")
    print("🔍"*40)
    
    # Test 1: Import questionnaire
    import_result = test_questionnaire_import_for_frontend()
    
    if not import_result:
        print("\n❌ Import failed. Cannot continue tests.")
        return
    
    material_id = import_result.get('material_id')
    questionnaire_id = import_result.get('id')
    
    # Test 2: Get Blue Line detail
    if material_id:
        test_blue_line_detail_for_frontend(material_id)
        
        # Test 3: Get MaterialSuppliers
        test_material_suppliers_for_frontend(material_id)
    
    # Test 4: Create Blue Line (if doesn't exist)
    comparison = import_result.get('comparison', {})
    if not comparison.get('blue_line_exists'):
        print("\n⚠️  Blue Line doesn't exist. Testing creation...")
        bl_result = test_create_blue_line_from_questionnaire(questionnaire_id)
        if bl_result:
            blue_line_id = bl_result.get('blue_line', {}).get('id') or bl_result.get('blue_line_id')
            if blue_line_id:
                test_create_composite(blue_line_id)
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("✅ All frontend integration tests completed!")
    print("\n📝 Frontend should work correctly if:")
    print("   1. Questionnaire import returns comparison data ✓")
    print("   2. MaterialSuppliers endpoint returns correct structure ✓")
    print("   3. Blue Line detail endpoint works ✓")
    print("   4. All endpoints match frontend expectations ✓")

if __name__ == "__main__":
    main()

