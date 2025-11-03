#!/usr/bin/env python3
"""
Test de extracción de PDF usando la configuración del sistema
Ejecuta: python test_pdf_extraction.py path/to/pdf
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

def test_extraction(pdf_path: str):
    """Probar extracción con la configuración actual"""
    print("="*80)
    print("  🧪 TEST DE EXTRACCIÓN DE PDF")
    print("="*80)
    print()
    
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"❌ Archivo no encontrado: {pdf_path}")
        return
    
    print(f"📄 PDF: {pdf_file.name}")
    print(f"   Path: {pdf_file.resolve()}")
    print()
    
    # Verificar configuración
    from app.core.config import settings
    
    use_openai = settings.USE_OPENAI_FOR_EXTRACTION and settings.OPENAI_API_KEY
    
    if use_openai:
        print("🤖 Método: OpenAI Vision API")
        print(f"   API Key: {settings.OPENAI_API_KEY[:10]}...")
    else:
        print("🔧 Método: OCR Local (Tesseract)")
        if not settings.OPENAI_API_KEY:
            print("   ⚠️  OpenAI no configurado")
        else:
            print("   ⚠️  OpenAI configurado pero desactivado")
    
    print()
    print("="*80)
    print("  EXTRAYENDO COMPOSICIÓN...")
    print("="*80)
    print()
    
    try:
        if use_openai:
            # Usar OpenAI
            from app.services.composite_extractor_openai import CompositeExtractorOpenAI
            
            print("🔄 Iniciando extracción con OpenAI Vision API...")
            print("   (Esto puede tomar 10-30 segundos...)")
            print()
            
            extractor = CompositeExtractorOpenAI(api_key=settings.OPENAI_API_KEY)
            components, confidence = extractor.extract_from_pdfs([str(pdf_file)], use_vision=True)
            
        else:
            # Usar OCR local
            from app.services.composite_extractor_ai import CompositeExtractorAI
            
            print("🔄 Iniciando extracción con OCR local...")
            print()
            
            extractor = CompositeExtractorAI()
            components, confidence = extractor.extract_from_pdfs([str(pdf_file)])
        
        # Mostrar resultados
        print("="*80)
        print("  ✅ RESULTADOS")
        print("="*80)
        print()
        
        print(f"📊 Componentes encontrados: {len(components)}")
        print(f"🎯 Confianza: {confidence:.1f}%")
        print()
        
        if components:
            print("📋 COMPONENTES EXTRAÍDOS:")
            print("-" * 80)
            
            total_percentage = 0
            for i, comp in enumerate(components, 1):
                name = comp.get('component_name', 'N/A')
                cas = comp.get('cas_number', 'N/A')
                perc = comp.get('percentage', 0)
                total_percentage += perc
                
                print(f"\n{i:2d}. {name}")
                print(f"     CAS: {cas}")
                print(f"     Porcentaje: {perc:.2f}%")
            
            print()
            print("-" * 80)
            print(f"📊 TOTAL PORCENTAJE: {total_percentage:.2f}%")
            
            if 95 <= total_percentage <= 105:
                print("   ✅ Porcentaje válido (rango aceptable: 95-105%)")
            elif total_percentage < 95:
                print(f"   ⚠️  Porcentaje bajo (faltan {100-total_percentage:.2f}%)")
            else:
                print(f"   ⚠️  Porcentaje alto (exceso de {total_percentage-100:.2f}%)")
            
            print()
            print("="*80)
            print("  💾 EXPORTAR RESULTADOS")
            print("="*80)
            print()
            
            # Guardar resultados en JSON
            import json
            output_file = pdf_file.parent / f"{pdf_file.stem}_extracted.json"
            results = {
                "source_pdf": str(pdf_file),
                "extraction_method": "OPENAI_VISION" if use_openai else "OCR_LOCAL",
                "confidence": confidence,
                "total_percentage": total_percentage,
                "components_count": len(components),
                "components": components
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Resultados guardados en: {output_file}")
            
        else:
            print("⚠️  No se encontraron componentes en el PDF")
            print()
            print("Posibles razones:")
            print("  - El PDF no contiene tabla de composición")
            print("  - El formato no es reconocible")
            print("  - El PDF está protegido o corrupto")
            print()
            print("💡 Intenta con OpenAI para mejor precisión:")
            print("   Cambia USE_OPENAI_FOR_EXTRACTION=true en .env")
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print()
        if "openai" in str(e).lower():
            print("💡 Instala OpenAI:")
            print("   pip install openai")
        elif "fitz" in str(e).lower() or "pytesseract" in str(e).lower():
            print("💡 Instala dependencias de OCR:")
            print("   pip install PyMuPDF pytesseract pdf2image Pillow opencv-python")
            
    except Exception as e:
        print(f"❌ Error durante extracción: {e}")
        import traceback
        print()
        print("📋 Detalles del error:")
        traceback.print_exc()

def main():
    if len(sys.argv) < 2:
        print("Uso: python test_pdf_extraction.py <path_to_pdf>")
        print()
        print("Ejemplo:")
        print("  python test_pdf_extraction.py ../data/pdfs/test.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    test_extraction(pdf_path)

if __name__ == "__main__":
    main()



