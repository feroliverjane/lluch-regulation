#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test End-to-End: Flujo completo de subida de TDS y extracción automática en Blue Line
Simula: Upload PDF → Auto Extract Composite → Verify Results
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.core.config import settings
from app.models.material import Material
from app.models.blue_line import BlueLine
from app.models.composite import Composite, CompositeComponent
import httpx

# URLs del API
API_BASE_URL = "http://localhost:8000/api"

def print_section(title: str):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def test_blue_line_composite_extraction():
    """Test completo de extracción de composite desde Blue Line"""
    
    print_section("🧪 TEST: Extracción Automática de Composite desde Blue Line")
    
    # 0. Verificar que el servidor esté corriendo
    print("0️⃣ Verificando conexión con el servidor...")
    try:
        with httpx.Client(timeout=5.0) as client:
            # Intentar hacer una petición simple
            test_response = client.get(f"{API_BASE_URL}/materials", timeout=5.0)
            if test_response.status_code == 200:
                print("✅ Servidor respondiendo correctamente")
            else:
                print(f"⚠️  Servidor responde con status: {test_response.status_code}")
    except httpx.ConnectError:
        print("❌ No se puede conectar al servidor")
        print("   💡 Asegúrate de que el servidor esté corriendo:")
        print("      cd backend && source venv/bin/activate && uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"⚠️  Error verificando servidor: {e}")
    
    # 1. Buscar material de lavanda
    print("\n1️⃣ Buscando material LAVANDA9999...")
    try:
        with httpx.Client(timeout=30.0) as client:
            materials_response = client.get(f"{API_BASE_URL}/materials")
            materials_response.raise_for_status()
            materials = materials_response.json()
        
        if not materials:
            print("⚠️  No hay materiales en la base de datos")
            print("   💡 Necesitas importar el cuestionario JSON primero")
            print("   📄 Archivo: data/questionnaires/ejemplo_material_nuevo_lavanda.json")
            return False
        
        print(f"   Total materiales encontrados: {len(materials)}")
        lavanda_material = None
        for mat in materials:
            if mat.get("reference_code") == "LAVANDA9999":
                lavanda_material = mat
                break
        
        if not lavanda_material:
            print("❌ Material LAVANDA9999 no encontrado")
            print("   💡 Necesitas importar el cuestionario JSON primero")
            print("   📄 Archivo: data/questionnaires/ejemplo_material_nuevo_lavanda.json")
            print("   🔧 Desde el frontend: /questionnaire-import")
            print(f"\n   Materiales disponibles: {', '.join([m.get('reference_code', 'N/A') for m in materials[:5]])}...")
            return False
        
        print(f"✅ Material encontrado: {lavanda_material['name']} (ID: {lavanda_material['id']})")
        material_id = lavanda_material['id']
        
    except Exception as e:
        print(f"❌ Error buscando material: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 2. Buscar Blue Line asociada
    print("\n2️⃣ Buscando Blue Line del material...")
    try:
        with httpx.Client(timeout=30.0) as client:
            bl_response = client.get(f"{API_BASE_URL}/blue-line/material/{material_id}")
            if bl_response.status_code == 404:
                print("❌ Blue Line no encontrada para este material")
                print("   💡 Necesitas crear la Blue Line desde el cuestionario primero")
                return False
            
            bl_response.raise_for_status()
            blue_line = bl_response.json()
            print(f"✅ Blue Line encontrada: ID {blue_line['id']}")
            blue_line_id = blue_line['id']
        
    except Exception as e:
        print(f"❌ Error buscando Blue Line: {e}")
        return False
    
    # 3. Verificar que existe el TDS
    print("\n3️⃣ Verificando archivo TDS...")
    tds_path = Path(__file__).parent.parent / "data" / "pdfs" / "TDS_LAVANDA9999_Lavender_Oil.pdf"
    
    if not tds_path.exists():
        print(f"❌ TDS no encontrado en: {tds_path}")
        print("   💡 Ejecuta primero: python scripts/generate_tds_lavanda.py")
        return False
    
    print(f"✅ TDS encontrado: {tds_path}")
    print(f"   Tamaño: {tds_path.stat().st_size / 1024:.1f} KB")
    
    # 4. Subir documento PDF
    print("\n4️⃣ Subiendo documento PDF a Blue Line...")
    try:
        with httpx.Client(timeout=60.0) as client:
            with open(tds_path, 'rb') as f:
                files = {'files': ('TDS_LAVANDA9999_Lavender_Oil.pdf', f, 'application/pdf')}
                upload_response = client.post(
                    f"{API_BASE_URL}/blue-line/{blue_line_id}/upload-documents",
                    files=files
                )
                upload_response.raise_for_status()
                upload_data = upload_response.json()
            
            print(f"✅ Documentos subidos exitosamente")
            print(f"   Total documentos: {upload_data.get('total_documents', 0)}")
            print(f"   Archivos subidos: {len(upload_data.get('uploaded_files', []))}")
            
            # Verificar que se guardaron en metadata
            bl_check = client.get(f"{API_BASE_URL}/blue-line/{blue_line_id}")
            bl_check.raise_for_status()
            bl_data = bl_check.json()
            
            pending_docs = bl_data.get('calculation_metadata', {}).get('pending_documents', [])
            print(f"   Documentos pendientes en metadata: {len(pending_docs)}")
            
            if len(pending_docs) == 0:
                print("⚠️  Advertencia: No se encontraron documentos pendientes en metadata")
        
    except httpx.HTTPStatusError as e:
        print(f"❌ Error HTTP subiendo documentos: {e.response.status_code}")
        try:
            error_detail = e.response.json()
            print(f"   Detalle: {error_detail}")
        except:
            print(f"   Response: {e.response.text[:500]}")
        return False
    except Exception as e:
        print(f"❌ Error subiendo documentos: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. Extraer composite automáticamente
    print("\n5️⃣ Extrayendo composite con IA...")
    print("   (Esto puede tomar 10-30 segundos...)")
    try:
        with httpx.Client(timeout=120.0) as client:  # Timeout largo para IA
            extract_response = client.post(
                f"{API_BASE_URL}/blue-line/{blue_line_id}/extract-composite"
            )
            extract_response.raise_for_status()
            extract_data = extract_response.json()
            
            print(f"✅ Composite extraído exitosamente!")
            print(f"   Composite ID: {extract_data.get('composite_id')}")
            print(f"   Componentes encontrados: {extract_data.get('components_count', 0)}")
            print(f"   Confianza: {extract_data.get('extraction_confidence', 0):.1f}%")
            print(f"   Método: {extract_data.get('extraction_method', 'N/A')}")
        
    except httpx.HTTPStatusError as e:
        print(f"❌ Error HTTP extrayendo composite: {e.response.status_code}")
        try:
            error_detail = e.response.json()
            print(f"   Detalle: {error_detail.get('detail', error_detail)}")
        except:
            print(f"   Response: {e.response.text[:500]}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Error extrayendo composite: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 6. Verificar composite creado
    print("\n6️⃣ Verificando composite creado...")
    try:
        composite_id = extract_data.get('composite_id')
        if not composite_id:
            print("⚠️  No se obtuvo composite_id de la respuesta")
            return False
        
        with httpx.Client(timeout=30.0) as client:
            composite_response = client.get(f"{API_BASE_URL}/composites/{composite_id}")
            composite_response.raise_for_status()
            composite = composite_response.json()
            
            print(f"✅ Composite verificado:")
            print(f"   ID: {composite['id']}")
            print(f"   Tipo: {composite.get('composite_type', 'N/A')}")
            print(f"   Origen: {composite.get('origin', 'N/A')}")
            print(f"   Confianza: {composite.get('extraction_confidence', 0):.1f}%")
            print(f"   Componentes: {len(composite.get('components', []))}")
            
            # Mostrar algunos componentes
            components = composite.get('components', [])
            if components:
                print(f"\n   Primeros componentes extraídos:")
                for i, comp in enumerate(components[:5], 1):
                    name = comp.get('component_name', 'N/A')
                    cas = comp.get('cas_number', 'N/A')
                    pct = comp.get('percentage', 0)
                    print(f"   {i}. {name} (CAS: {cas}) - {pct:.2f}%")
            
            # Verificar que Blue Line tiene referencia al composite
            bl_final = client.get(f"{API_BASE_URL}/blue-line/{blue_line_id}")
            bl_final.raise_for_status()
            bl_final_data = bl_final.json()
            
            if bl_final_data.get('composite_id') == composite_id:
                print(f"\n✅ Blue Line actualizada correctamente con composite_id: {composite_id}")
            else:
                print(f"\n⚠️  Blue Line no tiene referencia al composite (composite_id: {bl_final_data.get('composite_id')})")
        
    except Exception as e:
        print(f"❌ Error verificando composite: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print_section("✅ TEST COMPLETADO EXITOSAMENTE")
    print("📊 Resumen:")
    print(f"   • Material: {lavanda_material['name']} ({lavanda_material['reference_code']})")
    print(f"   • Blue Line ID: {blue_line_id}")
    print(f"   • Composite ID: {composite_id}")
    print(f"   • Componentes extraídos: {len(components)}")
    print(f"   • Confianza: {composite.get('extraction_confidence', 0):.1f}%")
    
    return True

if __name__ == "__main__":
    print("\n" + "="*80)
    print("  🧪 TEST: Extracción Automática de Composite desde Blue Line")
    print("="*80)
    print("\nEste test simula el flujo completo:")
    print("  1. Busca el material LAVANDA9999")
    print("  2. Encuentra su Blue Line")
    print("  3. Sube el TDS PDF")
    print("  4. Extrae automáticamente el composite con IA")
    print("  5. Verifica los resultados\n")
    
    success = test_blue_line_composite_extraction()
    
    if success:
        print("\n✅ Test completado exitosamente!")
        sys.exit(0)
    else:
        print("\n❌ Test falló. Revisa los errores arriba.")
        sys.exit(1)

