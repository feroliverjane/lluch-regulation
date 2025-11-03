"""
Script de diagnóstico para problemas con extracción de PDFs
Ejecuta: python diagnose_pdf_error.py
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

def check_dependencies():
    """Verificar que todas las dependencias estén instaladas"""
    print("="*80)
    print("1. VERIFICANDO DEPENDENCIAS")
    print("="*80)
    
    issues = []
    
    # Check PyMuPDF
    try:
        import fitz
        print("✅ PyMuPDF (fitz) instalado")
        print(f"   Versión: {fitz.version}")
    except ImportError:
        print("❌ PyMuPDF NO instalado")
        issues.append("pip install PyMuPDF")
    
    # Check pytesseract
    try:
        import pytesseract
        print("✅ pytesseract instalado")
        try:
            version = pytesseract.get_tesseract_version()
            print(f"   Tesseract versión: {version}")
        except Exception as e:
            print(f"⚠️  Tesseract instalado pero no accesible: {e}")
            issues.append("Verificar instalación de Tesseract OCR")
    except ImportError:
        print("❌ pytesseract NO instalado")
        issues.append("pip install pytesseract")
    
    # Check pdf2image
    try:
        from pdf2image import convert_from_path
        print("✅ pdf2image instalado")
    except ImportError:
        print("❌ pdf2image NO instalado")
        issues.append("pip install pdf2image")
    
    # Check PIL/Pillow
    try:
        from PIL import Image
        print("✅ Pillow instalado")
    except ImportError:
        print("❌ Pillow NO instalado")
        issues.append("pip install Pillow")
    
    # Check OpenCV
    try:
        import cv2
        print("✅ OpenCV instalado")
    except ImportError:
        print("❌ OpenCV NO instalado")
        issues.append("pip install opencv-python")
    
    return issues

def check_tesseract_path():
    """Verificar que Tesseract esté en el PATH"""
    print("\n" + "="*80)
    print("2. VERIFICANDO TESSERACT OCR")
    print("="*80)
    
    import pytesseract
    import subprocess
    
    try:
        # Try to get version
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract encontrado: versión {version}")
        
        # Check if tesseract command works
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Comando 'tesseract' funciona desde terminal")
        else:
            print("⚠️  Comando 'tesseract' no funciona")
            
    except Exception as e:
        print(f"❌ Tesseract NO encontrado: {e}")
        print("\n💡 Soluciones:")
        print("   macOS: brew install tesseract")
        print("   Ubuntu: sudo apt-get install tesseract-ocr")
        print("   Windows: Descargar de https://github.com/UB-Mannheim/tesseract/wiki")
        return False
    
    return True

def check_upload_directory():
    """Verificar directorio de uploads"""
    print("\n" + "="*80)
    print("3. VERIFICANDO DIRECTORIO DE UPLOADS")
    print("="*80)
    
    from app.core.config import settings
    
    upload_dir = Path(settings.UPLOAD_DIR)
    print(f"📁 Directorio configurado: {upload_dir}")
    print(f"   Path absoluto: {upload_dir.resolve()}")
    
    if upload_dir.exists():
        print("✅ Directorio existe")
        
        # Check permissions
        if upload_dir.is_dir():
            print("✅ Es un directorio")
            
            # Try to create a test file
            test_file = upload_dir / ".test_write"
            try:
                test_file.write_text("test")
                test_file.unlink()
                print("✅ Permisos de escritura OK")
            except Exception as e:
                print(f"❌ Sin permisos de escritura: {e}")
        else:
            print("❌ No es un directorio")
    else:
        print("⚠️  Directorio NO existe")
        print(f"   Creando directorio...")
        try:
            upload_dir.mkdir(parents=True, exist_ok=True)
            print("✅ Directorio creado")
        except Exception as e:
            print(f"❌ Error creando directorio: {e}")

def test_pdf_extraction():
    """Probar extracción de un PDF de ejemplo"""
    print("\n" + "="*80)
    print("4. PROBANDO EXTRACCIÓN DE PDF")
    print("="*80)
    
    # Buscar PDFs en el directorio de uploads
    from app.core.config import settings
    upload_dir = Path(settings.UPLOAD_DIR)
    
    pdf_files = list(upload_dir.rglob("*.pdf"))
    
    if not pdf_files:
        print("⚠️  No se encontraron PDFs en el directorio de uploads")
        print(f"   Buscando en: {upload_dir.resolve()}")
        print("\n💡 Sube un PDF primero usando el endpoint /upload-documents")
        return
    
    print(f"📄 Encontrados {len(pdf_files)} PDF(s):")
    for pdf in pdf_files[:5]:  # Mostrar solo los primeros 5
        print(f"   - {pdf}")
    
    # Probar con el primer PDF
    test_pdf = pdf_files[0]
    print(f"\n🧪 Probando extracción de: {test_pdf.name}")
    
    try:
        from app.services.composite_extractor_ai import CompositeExtractorAI
        
        extractor = CompositeExtractorAI()
        components, confidence = extractor.extract_from_pdfs([str(test_pdf)])
        
        print(f"✅ Extracción exitosa!")
        print(f"   Componentes encontrados: {len(components)}")
        print(f"   Confianza: {confidence:.1f}%")
        
        if components:
            print("\n   Componentes extraídos:")
            for i, comp in enumerate(components[:5], 1):  # Mostrar primeros 5
                print(f"   {i}. {comp.get('component_name', 'N/A')}")
                print(f"      CAS: {comp.get('cas_number', 'N/A')}")
                print(f"      %: {comp.get('percentage', 0):.2f}%")
        else:
            print("⚠️  No se encontraron componentes en el PDF")
            print("   El PDF puede no tener formato de composición reconocible")
            
    except Exception as e:
        print(f"❌ Error en extracción: {e}")
        import traceback
        print("\n📋 Traceback completo:")
        traceback.print_exc()

def check_database_attachments():
    """Verificar documentos adjuntos en base de datos"""
    print("\n" + "="*80)
    print("5. VERIFICANDO DOCUMENTOS EN BASE DE DATOS")
    print("="*80)
    
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.models.questionnaire import Questionnaire
        from app.core.database import Base
        from app.core.config import settings
        
        # Create session
        engine = create_engine(settings.DATABASE_URL.replace('postgresql://', 'sqlite:///').replace('@localhost:5432/lluch_regulation', '/app.db'))
        if 'sqlite' not in settings.DATABASE_URL:
            # Try to connect to actual DB
            try:
                engine = create_engine(settings.DATABASE_URL)
            except:
                # Fallback to SQLite if exists
                db_path = Path(__file__).parent / "app.db"
                if db_path.exists():
                    engine = create_engine(f"sqlite:///{db_path}")
                else:
                    print("⚠️  No se pudo conectar a la base de datos")
                    return
        
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        # Find questionnaires with attachments
        questionnaires = db.query(Questionnaire).filter(
            Questionnaire.attached_documents.isnot(None)
        ).limit(5).all()
        
        if not questionnaires:
            print("⚠️  No se encontraron cuestionarios con documentos adjuntos")
            return
        
        print(f"📋 Encontrados {len(questionnaires)} cuestionario(s) con documentos:")
        
        for q in questionnaires:
            print(f"\n   Cuestionario ID: {q.id}")
            print(f"   Material ID: {q.material_id}")
            
            if q.attached_documents:
                print(f"   Documentos adjuntos: {len(q.attached_documents)}")
                for doc in q.attached_documents[:3]:  # Primeros 3
                    print(f"      - {doc.get('filename', 'N/A')}")
                    print(f"        Path: {doc.get('path', 'N/A')}")
                    
                    # Verificar si el archivo existe
                    doc_path = Path(doc.get('path', ''))
                    if doc_path.exists():
                        print(f"        ✅ Archivo existe en disco")
                    else:
                        print(f"        ❌ Archivo NO existe en disco")
                        print(f"           Path buscado: {doc_path.resolve()}")
        
        db.close()
        
    except Exception as e:
        print(f"⚠️  Error verificando base de datos: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Ejecutar todos los diagnósticos"""
    print("\n" + "="*80)
    print("  🔍 DIAGNÓSTICO DE PROBLEMAS CON EXTRACCIÓN DE PDFs")
    print("="*80 + "\n")
    
    # 1. Dependencies
    dep_issues = check_dependencies()
    
    # 2. Tesseract
    tesseract_ok = check_tesseract_path()
    
    # 3. Upload directory
    check_upload_directory()
    
    # 4. Database attachments
    check_database_attachments()
    
    # 5. Test extraction
    test_pdf_extraction()
    
    # Summary
    print("\n" + "="*80)
    print("  📊 RESUMEN")
    print("="*80)
    
    if dep_issues:
        print("\n❌ PROBLEMAS ENCONTRADOS:")
        for issue in dep_issues:
            print(f"   - {issue}")
    else:
        print("\n✅ Todas las dependencias están instaladas")
    
    if not tesseract_ok:
        print("\n❌ Tesseract OCR no está disponible")
        print("   Esto es necesario para procesar PDFs escaneados")
    
    print("\n💡 Si sigues teniendo problemas:")
    print("   1. Verifica los logs del backend (terminal donde corre uvicorn)")
    print("   2. Asegúrate de subir PDFs ANTES de extraer composite")
    print("   3. Verifica que los PDFs tengan formato de composición química")
    print("   4. Revisa TROUBLESHOOTING_AI_VALIDATION.md para más detalles")

if __name__ == "__main__":
    main()



