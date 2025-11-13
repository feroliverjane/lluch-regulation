"""
Script de prueba para extracción con OpenAI
Ejecuta: python test_openai_extraction.py path/to/test.pdf
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

def test_openai_extraction(pdf_path: str, api_key: str = None):
    """Probar extracción con OpenAI"""
    print("="*80)
    print("🧪 PROBANDO EXTRACCIÓN CON OPENAI VISION")
    print("="*80)
    
    try:
        from app.services.composite_extractor_openai import CompositeExtractorOpenAI
        
        extractor = CompositeExtractorOpenAI(api_key=api_key)
        components, confidence = extractor.extract_from_pdfs([pdf_path], use_vision=True)
        
        print(f"\n✅ Extracción exitosa!")
        print(f"   Componentes encontrados: {len(components)}")
        print(f"   Confianza: {confidence:.1f}%")
        
        if components:
            print("\n📋 Componentes extraídos:")
            total_percentage = 0
            for i, comp in enumerate(components, 1):
                name = comp.get('component_name', 'N/A')
                cas = comp.get('cas_number', 'N/A')
                perc = comp.get('percentage', 0)
                total_percentage += perc
                
                print(f"\n   {i}. {name}")
                print(f"      CAS: {cas}")
                print(f"      Porcentaje: {perc:.2f}%")
            
            print(f"\n📊 Total porcentaje: {total_percentage:.2f}%")
            if 95 <= total_percentage <= 105:
                print("   ✅ Porcentaje válido (95-105%)")
            else:
                print("   ⚠️  Porcentaje fuera del rango esperado")
        else:
            print("⚠️  No se encontraron componentes")
            
    except ImportError as e:
        print(f"❌ Error: {e}")
        print("\n💡 Instala OpenAI:")
        print("   pip install openai")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_ocr_extraction(pdf_path: str):
    """Probar extracción con OCR local"""
    print("\n" + "="*80)
    print("🔧 PROBANDO EXTRACCIÓN CON OCR LOCAL")
    print("="*80)
    
    try:
        from app.services.composite_extractor_ai import CompositeExtractorAI
        
        extractor = CompositeExtractorAI()
        components, confidence = extractor.extract_from_pdfs([pdf_path])
        
        print(f"\n✅ Extracción exitosa!")
        print(f"   Componentes encontrados: {len(components)}")
        print(f"   Confianza: {confidence:.1f}%")
        
        if components:
            print("\n📋 Componentes extraídos:")
            total_percentage = 0
            for i, comp in enumerate(components[:10], 1):  # Mostrar primeros 10
                name = comp.get('component_name', 'N/A')
                cas = comp.get('cas_number', 'N/A')
                perc = comp.get('percentage', 0)
                total_percentage += perc
                
                print(f"\n   {i}. {name}")
                print(f"      CAS: {cas}")
                print(f"      Porcentaje: {perc:.2f}%")
            
            print(f"\n📊 Total porcentaje: {total_percentage:.2f}%")
        else:
            print("⚠️  No se encontraron componentes")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    if len(sys.argv) < 2:
        print("Uso: python test_openai_extraction.py <path_to_pdf> [openai_api_key]")
        print("\nEjemplo:")
        print("  python test_openai_extraction.py test.pdf")
        print("  python test_openai_extraction.py test.pdf sk-tu-api-key")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not Path(pdf_path).exists():
        print(f"❌ Archivo no encontrado: {pdf_path}")
        sys.exit(1)
    
    # Test OpenAI if API key provided
    if len(sys.argv) >= 3:
        api_key = sys.argv[2]
        test_openai_extraction(pdf_path, api_key)
    else:
        print("⚠️  No se proporcionó API key de OpenAI")
        print("   Probando solo con OCR local...\n")
    
    # Test OCR local
    test_ocr_extraction(pdf_path)
    
    print("\n" + "="*80)
    print("💡 Para usar OpenAI, agrega tu API key:")
    print("   python test_openai_extraction.py test.pdf sk-tu-api-key")
    print("="*80)

if __name__ == "__main__":
    main()













