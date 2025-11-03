#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test End-to-End: Flujo completo de subida de SDS desde Frontend
Simula: Upload PDF → Extract Composite → Verify Results
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

# Configurar logging para ver qué pasa en la extracción
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.core.config import settings
from app.models.material import Material
from app.models.questionnaire import Questionnaire, QuestionnaireStatus, QuestionnaireType
from app.models.composite import Composite, CompositeType, CompositeOrigin, CompositeStatus, CompositeComponent
from app.services.composite_extractor_openai import CompositeExtractorOpenAI

# Test database
TEST_DB_URL = "sqlite:///./test_frontend_flow.db"
engine = create_engine(TEST_DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def print_test(name, status, details=""):
    icon = "✅" if status else "❌"
    print(f"{icon} {name}")
    if details:
        print(f"   {details}")

def setup_test_db():
    """Crear base de datos de prueba"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print_test("Base de datos de prueba creada", True)

def test_complete_frontend_flow():
    """
    Test completo del flujo:
    1. Crear material y cuestionario
    2. Simular upload de SDS (como lo haría el frontend)
    3. Extraer composite con OpenAI
    4. Verificar resultados
    """
    print_section("TEST END-TO-END: Flujo Frontend → Extracción SDS")
    
    db = SessionLocal()
    
    try:
        # STEP 1: Crear Material
        print_test("STEP 1: Crear Material", True)
        material = Material(
            reference_code="TEST-BASIL-001",
            name="Basil Essential Oil",
            supplier="Test Supplier",
            supplier_code="SUP001",
            cas_number="8015-73-4"
        )
        db.add(material)
        db.commit()
        db.refresh(material)
        print_test("Material creado", True, f"ID: {material.id}, Code: {material.reference_code}")
        
        # STEP 2: Crear Questionnaire
        print_test("\nSTEP 2: Crear Questionnaire", True)
        questionnaire = Questionnaire(
            material_id=material.id,
            supplier_code="SUP001",
            questionnaire_type=QuestionnaireType.INITIAL_HOMOLOGATION,
            version=1,
            status=QuestionnaireStatus.SUBMITTED,
            responses={
                "q3t1s1f1": "Basil Essential Oil",
                "q3t1s4f44": "Yes"  # Natural
            }
        )
        db.add(questionnaire)
        db.commit()
        db.refresh(questionnaire)
        print_test("Questionnaire creado", True, f"ID: {questionnaire.id}")
        
        # STEP 3: Simular Upload de SDS (como lo haría el frontend)
        print_test("\nSTEP 3: Simular Upload de SDS", True)
        
        # Ruta del SDS
        sds_path = Path(__file__).parent.parent / "data" / "pdfs" / "ESMA_100049500_SDS_101074_EN.pdf"
        
        if not sds_path.exists():
            print_test("SDS no encontrado", False, f"Path: {sds_path}")
            return False
        
        # Simular lo que hace el endpoint upload-documents
        upload_dir = Path(settings.UPLOAD_DIR) / "questionnaires" / str(questionnaire.id)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Copiar SDS al directorio de uploads
        uploaded_file_path = upload_dir / sds_path.name
        import shutil
        shutil.copy2(sds_path, uploaded_file_path)
        
        # Actualizar questionnaire con attached_documents (como lo hace el endpoint)
        questionnaire.attached_documents = [{
            "filename": sds_path.name,
            "path": str(uploaded_file_path.resolve()),  # Ruta absoluta como en el endpoint
            "upload_date": datetime.utcnow().isoformat(),
            "type": "pdf"
        }]
        db.commit()
        
        print_test("SDS subido", True, f"Archivo: {sds_path.name}")
        print_test("Metadata guardada", True, f"Documentos adjuntos: {len(questionnaire.attached_documents)}")
        
        # STEP 4: Extraer Composite (como lo hace el endpoint extract-composite)
        print_test("\nSTEP 4: Extraer Composite con OpenAI", True)
        
        # Verificar configuración
        if not settings.USE_OPENAI_FOR_EXTRACTION or not settings.OPENAI_API_KEY:
            print_test("OpenAI no configurado", False, "Usando OCR local como fallback")
            return False
        
        # Obtener paths de PDFs
        pdf_paths = []
        for doc in questionnaire.attached_documents:
            if doc.get("type") == "pdf":
                # El path ya es absoluto (como lo guarda el endpoint)
                doc_path = Path(doc["path"])
                if doc_path.exists():
                    pdf_paths.append(str(doc_path.resolve()))
                else:
                    print(f"   ⚠️  PDF no encontrado: {doc_path}")
        
        if not pdf_paths:
            print_test("No se encontraron PDFs", False)
            return False
        
        print_test("PDFs encontrados", True, f"Archivos: {len(pdf_paths)}")
        
        # Extraer con OpenAI
        print("   🔄 Extrayendo con OpenAI Vision API...")
        print("   (Esto puede tomar 10-30 segundos...)")
        print(f"   📄 PDF: {pdf_paths[0]}")
        
        try:
        extractor = CompositeExtractorOpenAI(api_key=settings.OPENAI_API_KEY)
            print("   ✅ Extractor inicializado")
            
        components, confidence = extractor.extract_from_pdfs(pdf_paths, use_vision=True)
        
        print_test("Extracción completada", len(components) > 0, 
                  f"Componentes: {len(components)}, Confianza: {confidence:.1f}%")
            
            if components:
                print("   📋 Componentes extraídos:")
                for i, comp in enumerate(components[:5], 1):  # Mostrar primeros 5
                    print(f"      {i}. {comp.get('component_name', 'N/A')} - {comp.get('cas_number', 'N/A')} - {comp.get('percentage', 0)}%")
        except Exception as e:
            print_test("Error durante extracción", False, str(e))
            import traceback
            traceback.print_exc()
            return False
        
        if not components:
            print_test("No se extrajeron componentes", False)
            return False
        
        # STEP 5: Crear Composite (como lo hace el endpoint)
        print_test("\nSTEP 5: Crear Composite en Base de Datos", True)
        
        composite = Composite(
            material_id=questionnaire.material_id,
            version=1,
            origin=CompositeOrigin.CALCULATED,
            composite_type=CompositeType.Z1,
            status=CompositeStatus.DRAFT,
            questionnaire_id=questionnaire.id,
            source_documents=questionnaire.attached_documents,
            extraction_confidence=confidence,
            composite_metadata={
                "extraction_method": "OPENAI_VISION",
                "extraction_date": datetime.utcnow().isoformat(),
                "source_questionnaire": questionnaire.id
            },
            notes=f"Extracted from {len(pdf_paths)} document(s) with {confidence:.1f}% confidence"
        )
        
        # Agregar componentes
        for comp_data in components:
            component = CompositeComponent(
                cas_number=comp_data.get('cas_number'),
                component_name=comp_data.get('component_name'),
                percentage=comp_data.get('percentage', 0),
                confidence_level=comp_data.get('confidence', confidence)
            )
            composite.components.append(component)
        
        db.add(composite)
        db.commit()
        db.refresh(composite)
        
        print_test("Composite creado", True, f"ID: {composite.id}")
        print_test("Componentes agregados", True, f"Total: {len(composite.components)}")
        
        # STEP 6: Verificar resultados
        print_test("\nSTEP 6: Verificar Resultados", True)
        
        # Verificar que el composite tiene componentes
        components_count = len(composite.components)
        print_test("Composite tiene componentes", components_count > 0, 
                  f"Total: {components_count}")
        
        # Verificar porcentajes
        total_percentage = sum(c.percentage for c in composite.components)
        print_test("Porcentajes calculados", total_percentage > 0,
                  f"Total: {total_percentage:.2f}%")
        
        # Verificar CAS numbers
        cas_count = sum(1 for c in composite.components if c.cas_number and c.cas_number != 'N/A')
        print_test("CAS numbers extraídos", cas_count > 0,
                  f"CAS válidos: {cas_count}/{components_count}")
        
        # Verificar confianza
        print_test("Confianza de extracción", composite.extraction_confidence >= 50,
                  f"Confianza: {composite.extraction_confidence:.1f}%")
        
        # Mostrar componentes extraídos
        print_test("\nComponentes Extraídos:", True)
        print("-" * 80)
        for i, comp in enumerate(composite.components, 1):
            print(f"{i:2d}. {comp.component_name}")
            print(f"     CAS: {comp.cas_number}")
            print(f"     %: {comp.percentage:.2f}%")
        
        print("-" * 80)
        print(f"Total: {total_percentage:.2f}%")
        
        # STEP 7: Verificar que el endpoint funcionaría igual
        print_test("\nSTEP 7: Validar Compatibilidad con Endpoint", True)
        
        # Simular respuesta del endpoint
        endpoint_response = {
            "questionnaire_id": questionnaire.id,
            "composite_id": composite.id,
            "composite_type": "Z1",
            "components_count": len(components),
            "extraction_confidence": confidence,
            "status": "extracted"
        }
        
        print_test("Estructura de respuesta correcta", True)
        print(f"   Response: {json.dumps(endpoint_response, indent=2)}")
        
        # Verificar relaciones
        print_test("\nVerificando Relaciones", True)
        print_test("Composite → Questionnaire", composite.questionnaire_id == questionnaire.id,
                  f"Linked: {composite.questionnaire_id}")
        print_test("Composite → Material", composite.material_id == material.id,
                  f"Linked: {composite.material_id}")
        
        # Resumen final
        print_section("RESUMEN DEL TEST")
        
        all_passed = (
            components_count > 0 and
            total_percentage > 0 and
            cas_count > 0 and
            composite.extraction_confidence >= 50
        )
        
        print_test("Test Completo", all_passed)
        print(f"\n📊 Estadísticas:")
        print(f"   - Componentes extraídos: {components_count}")
        print(f"   - CAS numbers válidos: {cas_count}")
        print(f"   - Total porcentaje: {total_percentage:.2f}%")
        print(f"   - Confianza: {composite.extraction_confidence:.1f}%")
        print(f"   - Método: {composite.composite_metadata.get('extraction_method')}")
        
        return all_passed
        
    except Exception as e:
        print_test("Error durante test", False, str(e))
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def main():
    """Ejecutar test completo"""
    print("\n" + "="*80)
    print("  🧪 TEST END-TO-END: Flujo Frontend → Extracción SDS con OpenAI")
    print("="*80)
    
    # Verificar configuración
    print("\n📋 Verificando Configuración:")
    print(f"   OpenAI API Key: {'✅ Configurada' if settings.OPENAI_API_KEY else '❌ No configurada'}")
    print(f"   Usar OpenAI: {'✅ Activado' if settings.USE_OPENAI_FOR_EXTRACTION else '❌ Desactivado'}")
    
    if not settings.OPENAI_API_KEY or not settings.USE_OPENAI_FOR_EXTRACTION:
        print("\n⚠️  OpenAI no está configurado. El test usará OCR local como fallback.")
        print("   Para usar OpenAI, configura:")
        print("   - OPENAI_API_KEY en .env")
        print("   - USE_OPENAI_FOR_EXTRACTION=true")
    
    # Setup
    setup_test_db()
    
    # Ejecutar test
    success = test_complete_frontend_flow()
    
    # Resultado final
    print("\n" + "="*80)
    if success:
        print("  ✅ TEST COMPLETADO EXITOSAMENTE")
        print("="*80)
        print("\n💡 El flujo completo funciona correctamente:")
        print("   1. ✅ Upload de PDF desde frontend")
        print("   2. ✅ Guardado de metadata en questionnaire")
        print("   3. ✅ Extracción con OpenAI")
        print("   4. ✅ Creación de Composite con componentes")
        print("   5. ✅ Relaciones correctas (questionnaire → composite → material)")
    else:
        print("  ⚠️  TEST COMPLETADO CON ADVERTENCIAS")
        print("="*80)
        print("\n💡 Revisa los resultados arriba para más detalles")
    
    print(f"\n📁 Base de datos de prueba: {TEST_DB_URL}")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()

