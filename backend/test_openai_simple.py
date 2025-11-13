#!/usr/bin/env python3
"""Test simple de extracción con OpenAI"""
import sys
sys.path.insert(0, '.')

from app.services.composite_extractor_openai import CompositeExtractorOpenAI
from app.core.config import settings
import fitz
import json

pdf_path = '../data/pdfs/ESMA_100049500_IFR_101074_EN.pdf'

print('='*80)
print('🧪 TEST DE EXTRACCIÓN CON OPENAI')
print('='*80)
print(f'📄 PDF: {pdf_path}')
print(f'🤖 Método: OpenAI GPT-4 (extracción de texto)')
print()

# Extraer texto del PDF
print('📖 Extrayendo texto del PDF...')
try:
    doc = fitz.open(pdf_path)
    text = ''
    for page in doc[:5]:  # Primeras 5 páginas
        text += page.get_text() + '\n'
    doc.close()
    print(f'✅ Texto extraído: {len(text)} caracteres')
    print(f'   Primeras líneas: {text[:200]}...')
    print()
except Exception as e:
    print(f'❌ Error extrayendo texto: {e}')
    sys.exit(1)

# Usar OpenAI con texto
print('🤖 Enviando a OpenAI para análisis...')
print('   (Esto puede tomar 10-30 segundos...)')
print()

try:
    extractor = CompositeExtractorOpenAI(api_key=settings.OPENAI_API_KEY)
    components, confidence = extractor._extract_with_text(pdf_path)
    
    print()
    print('='*80)
    print('✅ RESULTADOS')
    print('='*80)
    print(f'📊 Componentes encontrados: {len(components)}')
    print(f'🎯 Confianza: {confidence:.1f}%')
    print()
    
    if components:
        print('📋 COMPONENTES EXTRAÍDOS:')
        print('-'*80)
        total = 0
        for i, c in enumerate(components, 1):
            name = c.get('component_name', 'N/A')
            cas = c.get('cas_number', 'N/A')
            perc = c.get('percentage', 0)
            total += perc
            print(f'\n{i:2d}. {name}')
            print(f'     CAS: {cas}')
            print(f'     Porcentaje: {perc:.2f}%')
        
        print()
        print('-'*80)
        print(f'📊 TOTAL PORCENTAJE: {total:.2f}%')
        if 95 <= total <= 105:
            print('   ✅ Porcentaje válido (rango aceptable: 95-105%)')
        else:
            print(f'   ⚠️  Porcentaje fuera del rango esperado')
        
        # Guardar resultados
        output_file = '../data/pdfs/extracted_components.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'source_pdf': pdf_path,
                'components': components,
                'confidence': confidence,
                'total_percentage': total
            }, f, indent=2, ensure_ascii=False)
        print(f'\n💾 Resultados guardados en: {output_file}')
        
    else:
        print('⚠️  No se encontraron componentes en el PDF')
        print('\nPosibles razones:')
        print('  - El PDF no contiene tabla de composición química')
        print('  - El formato no es reconocible')
        print('  - La información está en formato no estructurado')
        
except Exception as e:
    print(f'\n❌ Error: {e}')
    import traceback
    traceback.print_exc()

print('\n' + '='*80)













