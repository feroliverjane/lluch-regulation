"""
Test script for Frontend AI Integration
Tests the new AI endpoints used by the frontend components
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000/api"

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def test_coherence_validation():
    """Test POST /questionnaires/{id}/validate-coherence"""
    print_section("TEST 1: Validación de Coherencia AI")
    
    # First, get a questionnaire ID
    response = requests.get(f"{BASE_URL}/questionnaires")
    questionnaires = response.json()
    
    if not questionnaires:
        print("❌ No hay cuestionarios disponibles para probar")
        return None
    
    questionnaire_id = questionnaires[0]["id"]
    print(f"📋 Usando cuestionario ID: {questionnaire_id}")
    
    # Validate coherence
    response = requests.post(f"{BASE_URL}/questionnaires/{questionnaire_id}/validate-coherence")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Coherence Score: {result.get('coherence_score')}/100")
        print(f"   Issues detectados: {len(result.get('coherence_details', []))}")
        
        for i, issue in enumerate(result.get('coherence_details', [])[:3], 1):
            print(f"   {i}. [{issue['severity']}] {issue['field']}: {issue['issue']}")
        
        return questionnaire_id
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None

def test_document_upload(questionnaire_id):
    """Test POST /questionnaires/{id}/upload-documents"""
    print_section("TEST 2: Upload de Documentos")
    
    # Create a dummy PDF file
    dummy_pdf = Path("test_document.pdf")
    dummy_pdf.write_bytes(b"%PDF-1.4\nDummy PDF content")
    
    try:
        with open(dummy_pdf, 'rb') as f:
            files = {'files': ('test_document.pdf', f, 'application/pdf')}
            response = requests.post(
                f"{BASE_URL}/questionnaires/{questionnaire_id}/upload-documents",
                files=files
            )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Documentos subidos: {len(result.get('uploaded_files', []))}")
            for doc in result.get('uploaded_files', []):
                print(f"   - {doc['filename']}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
    
    finally:
        # Cleanup
        if dummy_pdf.exists():
            dummy_pdf.unlink()

def test_composite_extraction(questionnaire_id):
    """Test POST /questionnaires/{id}/extract-composite"""
    print_section("TEST 3: Extracción de Composite con IA")
    
    response = requests.post(f"{BASE_URL}/questionnaires/{questionnaire_id}/extract-composite")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Composite extraído:")
        print(f"   ID: {result.get('composite_id')}")
        print(f"   Tipo: {result.get('composite_type')}")
        print(f"   Componentes: {result.get('components_count')}")
        print(f"   Confianza: {result.get('extraction_confidence', 0):.1f}%")
        return result.get('composite_id')
    else:
        print(f"⚠️  Esperado (si no hay docs): {response.status_code}")
        print(response.text[:200])
        return None

def test_get_questionnaire_composite(questionnaire_id):
    """Test GET /questionnaires/{id}/composite"""
    print_section("TEST 4: Obtener Composite de Cuestionario")
    
    response = requests.get(f"{BASE_URL}/questionnaires/{questionnaire_id}/composite")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Composite obtenido:")
        print(f"   ID: {result.get('id')}")
        print(f"   Tipo: {result.get('composite_type')}")
        print(f"   Componentes: {len(result.get('components', []))}")
    elif response.status_code == 404:
        print(f"⚠️  No hay composite asociado (esperado si no se extrajo)")
    else:
        print(f"❌ Error: {response.status_code}")

def test_create_blue_line(questionnaire_id):
    """Test POST /questionnaires/{id}/create-blue-line"""
    print_section("TEST 5: Crear Blue Line desde Cuestionario")
    
    # First check if questionnaire is approved
    response = requests.get(f"{BASE_URL}/questionnaires/{questionnaire_id}")
    questionnaire = response.json()
    
    if questionnaire.get('status') != 'APPROVED':
        print(f"⚠️  Cuestionario no está aprobado (status: {questionnaire.get('status')})")
        print("   Este endpoint solo funciona con cuestionarios aprobados")
        return None
    
    response = requests.post(f"{BASE_URL}/questionnaires/{questionnaire_id}/create-blue-line")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Blue Line creada:")
        print(f"   ID: {result.get('blue_line_id')}")
        print(f"   Material ID: {result.get('material_id')}")
        print(f"   Tipo: {result.get('material_type')}")
        return result.get('blue_line_id')
    else:
        print(f"⚠️  Error o Blue Line ya existe: {response.status_code}")
        print(response.text[:200])
        return None

def test_update_composite_to_z2(composite_id):
    """Test POST /composites/{id}/update-to-z2"""
    print_section("TEST 6: Actualizar Composite Z1 → Z2")
    
    if not composite_id:
        print("⚠️  No hay composite_id disponible para probar")
        return
    
    # Create dummy lab file
    dummy_file = Path("lab_analysis.pdf")
    dummy_file.write_bytes(b"%PDF-1.4\nLab Analysis")
    
    try:
        with open(dummy_file, 'rb') as f:
            files = {'file': ('lab_analysis.pdf', f, 'application/pdf')}
            response = requests.post(
                f"{BASE_URL}/composites/{composite_id}/update-to-z2",
                files=files
            )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Composite actualizado a Z2:")
            print(f"   ID: {result.get('composite_id')}")
            print(f"   Nuevo Tipo: {result.get('composite_type')}")
        else:
            print(f"⚠️  Error o ya es Z2: {response.status_code}")
            print(response.text[:200])
    
    finally:
        if dummy_file.exists():
            dummy_file.unlink()

def test_composite_comparison():
    """Test POST /composites/compare-detailed"""
    print_section("TEST 7: Comparación Detallada de Composites")
    
    # Get two composite IDs
    response = requests.get(f"{BASE_URL}/composites")
    composites = response.json()
    
    if len(composites) < 2:
        print("⚠️  Se necesitan al menos 2 composites para comparar")
        return
    
    composite1_id = composites[0]["id"]
    composite2_id = composites[1]["id"]
    
    print(f"📊 Comparando Composite #{composite1_id} vs #{composite2_id}")
    
    payload = {
        "composite1_id": composite1_id,
        "composite2_id": composite2_id
    }
    
    response = requests.post(f"{BASE_URL}/composites/compare-detailed", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Comparación completada:")
        print(f"   Match Score: {result.get('match_score', 0):.1f}%")
        print(f"   Componentes coincidentes: {result.get('matched_components')}")
        print(f"   Solo en C1: {len(result.get('only_in_composite1', []))}")
        print(f"   Solo en C2: {len(result.get('only_in_composite2', []))}")
        print(f"   Diferencias: {len(result.get('differences', []))}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text[:200])

def test_get_material_blue_line():
    """Test GET /materials/{id}/blue-line"""
    print_section("TEST 8: Obtener Blue Line por Material")
    
    # Get a material with blue line
    response = requests.get(f"{BASE_URL}/blue-line")
    blue_lines = response.json()
    
    if not blue_lines:
        print("⚠️  No hay Blue Lines disponibles")
        return
    
    material_id = blue_lines[0]["material_id"]
    
    response = requests.get(f"{BASE_URL}/materials/{material_id}/blue-line")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Blue Line obtenida:")
        print(f"   ID: {result.get('id')}")
        print(f"   Material ID: {result.get('material_id')}")
        print(f"   Tipo: {result.get('material_type')}")
        print(f"   Composite ID: {result.get('composite_id', 'N/A')}")
    else:
        print(f"❌ Error: {response.status_code}")

def main():
    print("="*80)
    print("  🧪 FRONTEND AI INTEGRATION TESTS")
    print("="*80)
    print("\nEste script prueba los nuevos endpoints usados por el frontend")
    print("Asegúrate de que el backend esté corriendo en http://localhost:8000\n")
    
    try:
        # Test 1: Coherence validation
        questionnaire_id = test_coherence_validation()
        
        if questionnaire_id:
            # Test 2: Document upload
            test_document_upload(questionnaire_id)
            
            # Test 3: Composite extraction
            composite_id = test_composite_extraction(questionnaire_id)
            
            # Test 4: Get questionnaire composite
            test_get_questionnaire_composite(questionnaire_id)
            
            # Test 5: Create blue line
            test_create_blue_line(questionnaire_id)
            
            # Test 6: Update to Z2
            if composite_id:
                test_update_composite_to_z2(composite_id)
        
        # Test 7: Composite comparison
        test_composite_comparison()
        
        # Test 8: Get material blue line
        test_get_material_blue_line()
        
        print_section("RESUMEN")
        print("✅ Tests completados. Revisa los resultados arriba.")
        print("⚠️  Algunos tests pueden fallar si no hay datos suficientes en la DB.")
        print("\n💡 Tip: Usa los scripts de prueba existentes para crear datos de prueba:")
        print("   python test_complete_user_flow.py")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: No se puede conectar al backend")
        print("   Asegúrate de que el servidor esté corriendo:")
        print("   cd backend && uvicorn app.main:app --reload")
    
    except Exception as e:
        print(f"\n❌ ERROR inesperado: {e}")

if __name__ == "__main__":
    main()












