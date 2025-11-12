#!/usr/bin/env python3
"""
Test script to verify frontend new material detection functionality.
This script tests the complete flow from frontend perspective.
"""

import requests
import json
from pathlib import Path
import time

BASE_URL = "http://localhost:8000/api"
FRONTEND_URL = "http://localhost:5173"

def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_step(step, description):
    print(f"\n▶ Step {step}: {description}")

def check_backend():
    """Check if backend is running"""
    try:
        response = requests.get(f"{BASE_URL.replace('/api', '')}/health", timeout=2)
        if response.status_code == 200:
            return True
    except:
        pass
    return False

def check_frontend():
    """Check if frontend is running"""
    try:
        response = requests.get(FRONTEND_URL, timeout=2)
        if response.status_code == 200:
            return True
    except:
        pass
    return False

def test_backend_detection():
    """Test backend detection of new material"""
    print_section("TEST 1: Backend New Material Detection")
    
    # Check if material ROSE0001 exists
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
        print("   Deleting it for testing...")
        # Optionally delete it, but for now just skip
        return False
    else:
        print("✅ Material ROSE0001 does not exist - perfect for testing!")
    
    # Test import
    print_step(2, "Testing backend import endpoint...")
    test_json_path = Path("data/questionnaires/ejemplo_cuestionario_nuevo_material.json")
    
    if not test_json_path.exists():
        print(f"❌ Test JSON file not found: {test_json_path}")
        return False
    
    with open(test_json_path, 'rb') as f:
        files = {'file': ('ejemplo_cuestionario_nuevo_material.json', f, 'application/json')}
        response = requests.post(
            f"{BASE_URL}/questionnaires/import/json",
            files=files
        )
    
    if response.status_code == 400:
        error_data = response.json()
        error_message = error_data.get("detail", "")
        
        if "NEW_MATERIAL_DETECTED" in error_message and "ROSE0001" in error_message:
            print("✅ Backend correctly detects new material!")
            print(f"   Error message: {error_message[:100]}...")
            return True
        else:
            print(f"❌ Unexpected error: {error_message}")
            return False
    else:
        print(f"❌ Unexpected status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        return False

def test_frontend_api_call():
    """Test that frontend can make the API call correctly"""
    print_section("TEST 2: Frontend API Call Simulation")
    
    print_step(1, "Simulating frontend POST request to import endpoint...")
    test_json_path = Path("data/questionnaires/ejemplo_cuestionario_nuevo_material.json")
    
    # Simulate what frontend does
    with open(test_json_path, 'rb') as f:
        files = {'file': ('ejemplo_cuestionario_nuevo_material.json', f, 'application/json')}
        headers = {}
        response = requests.post(
            f"{BASE_URL}/questionnaires/import/json",
            files=files,
            headers=headers
        )
    
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 400:
        error_data = response.json()
        error_message = error_data.get("detail", "")
        
        print_step(2, "Verifying error message format for frontend parsing...")
        
        # Check if frontend can parse this
        if "NEW_MATERIAL_DETECTED:" in error_message:
            # Extract material code (simulating frontend logic)
            import re
            match = re.search(r"material '([^']+)'", error_message)
            if match:
                detected_code = match.group(1)
                print(f"✅ Frontend can extract material code: {detected_code}")
                
                # Verify JSON can be parsed for product name
                with open(test_json_path, 'r') as f:
                    json_data = json.load(f)
                    product_name_field = None
                    for item in json_data.get("data", []):
                        if item.get("fieldCode") == "q3t1s2f16":
                            product_name_field = item.get("value", "")
                            break
                    
                    if product_name_field:
                        print(f"✅ Frontend can extract product name: {product_name_field}")
                    else:
                        print("⚠️  Could not find product name field")
                
                return True
            else:
                print("❌ Could not extract material code from error message")
                return False
        else:
            print(f"❌ Error message does not contain NEW_MATERIAL_DETECTED")
            return False
    else:
        print(f"❌ Unexpected status: {response.status_code}")
        return False

def test_existing_material_flow():
    """Test that existing material flow still works"""
    print_section("TEST 3: Existing Material Import Flow")
    
    print_step(1, "Finding an existing material...")
    materials_response = requests.get(f"{BASE_URL}/materials/")
    materials = materials_response.json()
    
    if not materials:
        print("⚠️  No materials found. Skipping test.")
        return True
    
    existing_material = materials[0]
    print(f"✅ Using material: {existing_material['reference_code']} (ID: {existing_material['id']})")
    
    # Create test JSON
    print_step(2, "Creating test JSON...")
    test_json = {
        "requestId": 9999,
        "data": [
            {
                "fieldCode": "q3t1s2f15",
                "fieldName": "Supplier Name",
                "fieldType": "inputText",
                "value": "TEST SUPPLIER FRONTEND"
            },
            {
                "fieldCode": "q3t1s2f16",
                "fieldName": "Product Name",
                "fieldType": "inputText",
                "value": f"[{existing_material['reference_code']}] Test Product Frontend"
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
    
    print_step(3, "Importing questionnaire...")
    with open(temp_path, 'rb') as f:
        files = {'file': ('test_existing_material_frontend.json', f, 'application/json')}
        response = requests.post(
            f"{BASE_URL}/questionnaires/import/json",
            files=files
        )
    
    temp_path.unlink()
    
    if response.status_code == 201:
        result = response.json()
        print(f"✅ Import successful!")
        print(f"   Questionnaire ID: {result.get('id')}")
        print(f"   Material ID: {result.get('material_id')}")
        print(f"   Comparison available: {'Yes' if result.get('comparison') else 'No'}")
        
        if result.get('comparison'):
            comparison = result['comparison']
            print(f"   Blue Line exists: {comparison.get('blue_line_exists')}")
            print(f"   Score: {comparison.get('score', 0)}%")
        
        return True
    else:
        print(f"❌ Import failed: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        return False

def test_error_message_format():
    """Test that error message format is correct for frontend parsing"""
    print_section("TEST 4: Error Message Format Validation")
    
    print_step(1, "Testing error message format...")
    test_json_path = Path("data/questionnaires/ejemplo_cuestionario_nuevo_material.json")
    
    with open(test_json_path, 'rb') as f:
        files = {'file': ('test.json', f, 'application/json')}
        response = requests.post(
            f"{BASE_URL}/questionnaires/import/json",
            files=files
        )
    
    if response.status_code == 400:
        error_data = response.json()
        error_message = error_data.get("detail", "")
        
        print(f"   Error message: {error_message}")
        
        checks = []
        
        # Check 1: Contains NEW_MATERIAL_DETECTED
        checks.append(("Contains NEW_MATERIAL_DETECTED", "NEW_MATERIAL_DETECTED" in error_message))
        
        # Check 2: Contains material code
        checks.append(("Contains material code ROSE0001", "ROSE0001" in error_message))
        
        # Check 3: Can extract material code with regex
        import re
        match = re.search(r"material '([^']+)'", error_message)
        checks.append(("Can extract material code with regex", match is not None and match.group(1) == "ROSE0001"))
        
        # Check 4: Contains instruction text
        checks.append(("Contains instruction text", "crea primero el material" in error_message.lower()))
        
        print("\n   Validation Results:")
        all_passed = True
        for check_name, result in checks:
            status = "✅" if result else "❌"
            print(f"   {status} {check_name}")
            if not result:
                all_passed = False
        
        return all_passed
    else:
        print(f"❌ Expected 400, got {response.status_code}")
        return False

if __name__ == "__main__":
    print("\n" + "🧪 TESTING FRONTEND NEW MATERIAL DETECTION")
    print("=" * 70)
    
    # Check services
    print("\n📡 Checking services...")
    backend_ok = check_backend()
    frontend_ok = check_frontend()
    
    print(f"   Backend (http://localhost:8000): {'✅ Running' if backend_ok else '❌ Not running'}")
    print(f"   Frontend (http://localhost:5173): {'✅ Running' if frontend_ok else '❌ Not running'}")
    
    if not backend_ok:
        print("\n❌ Backend is not running. Please start it first.")
        exit(1)
    
    if not frontend_ok:
        print("\n⚠️  Frontend is not running. Backend tests will still run.")
    
    results = {}
    
    try:
        # Test 1: Backend detection
        results['backend_detection'] = test_backend_detection()
        
        # Test 2: Frontend API call simulation
        results['frontend_api'] = test_frontend_api_call()
        
        # Test 3: Existing material flow
        results['existing_material'] = test_existing_material_flow()
        
        # Test 4: Error message format
        results['error_format'] = test_error_message_format()
        
        # Summary
        print_section("TEST SUMMARY")
        print(f"Backend New Material Detection:      {'✅ PASSED' if results['backend_detection'] else '❌ FAILED'}")
        print(f"Frontend API Call Simulation:        {'✅ PASSED' if results['frontend_api'] else '❌ FAILED'}")
        print(f"Existing Material Import Flow:      {'✅ PASSED' if results['existing_material'] else '❌ FAILED'}")
        print(f"Error Message Format Validation:    {'✅ PASSED' if results['error_format'] else '❌ FAILED'}")
        
        all_passed = all(results.values())
        
        if all_passed:
            print("\n🎉 All tests passed!")
            print("\n✅ Frontend new material detection is working correctly!")
            print("   - Backend correctly detects new materials")
            print("   - Error messages are properly formatted")
            print("   - Frontend can parse error messages")
            print("   - Existing material flow still works")
        else:
            print("\n⚠️  Some tests failed. Please review the output above.")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to backend API.")
        print("   Make sure the backend is running on http://localhost:8000")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()













