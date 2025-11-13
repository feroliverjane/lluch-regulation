#!/usr/bin/env python3
"""Test específico para extraer composición de SDS"""
import sys
sys.path.insert(0, '.')

from app.services.composite_extractor_openai import CompositeExtractorOpenAI
from app.core.config import settings
import fitz
import json

pdf_path = '../data/pdfs/ESMA_100049500_SDS_101074_EN.pdf'

print('='*80)
print('🧪 TEST SDS - SECCIÓN 3 COMPOSICIÓN')
print('='*80)

# Extraer texto completo
doc = fitz.open(pdf_path)
full_text = ''
for page in doc:
    full_text += page.get_text() + '\n'
doc.close()

# Encontrar sección 3
section3_start = full_text.find('3.     COMPOSITION')
if section3_start < 0:
    section3_start = full_text.find('COMPOSITION / INFORMATION')
    
if section3_start >= 0:
    # Extraer sección 3 completa
    section3_text = full_text[section3_start:section3_start+4000]
    print(f'\n📋 Sección 3 encontrada ({len(section3_text)} caracteres)')
    print('\nVista previa:')
    print('-'*80)
    print(section3_text[:800])
    print('...')
    print('-'*80)
    
    print('\n🤖 Enviando a OpenAI para extracción...')
    print('   (Esto puede tomar 10-30 segundos...)')
    
    extractor = CompositeExtractorOpenAI(api_key=settings.OPENAI_API_KEY)
    
    # Prompt específico para SDS Section 3
    response = extractor.client.chat.completions.create(
        model='gpt-4o',
        messages=[
            {
                'role': 'system',
                'content': '''You are an expert chemist extracting chemical composition from Safety Data Sheets Section 3.

Extract ALL chemical components from the composition table.

The table typically has columns:
- CAS# (CAS number)
- Substance (chemical name)
- Percent % (percentage)

Return ONLY a JSON object with this structure:
{
    "components": [
        {
            "component_name": "Full chemical name",
            "cas_number": "CAS number in format XXXXXXX-XX-X",
            "percentage": decimal_number
        }
    ]
}

Rules:
- Extract ALL components from the table
- CAS numbers format: XXXXXXX-XX-X
- If percentage is a range like [0-1], use midpoint (0.5)
- If percentage says "<X", use X/2
- Extract substance names exactly as written
- Include all components, even with small percentages'''
            },
            {
                'role': 'user',
                'content': f'''Extract ALL chemical components from this SDS Section 3:

{section3_text}

Return the JSON object with all components found.'''
            }
        ],
        response_format={'type': 'json_object'},
        temperature=0.1
    )
    
    result = json.loads(response.choices[0].message.content)
    
    # Extraer componentes
    if isinstance(result, dict) and 'components' in result:
        components = result['components']
    elif isinstance(result, list):
        components = result
    else:
        components = []
    
    print('\n' + '='*80)
    print('✅ RESULTADOS')
    print('='*80)
    print(f'📊 Componentes encontrados: {len(components)}')
    
    if components:
        print('\n📋 COMPONENTES EXTRAÍDOS:')
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
        elif total > 0:
            print(f'   ℹ️  Porcentaje: {total:.2f}% (puede ser parcial o con rangos)')
        
        # Guardar resultados
        output_file = '../data/pdfs/sds_extracted_components.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'source_pdf': pdf_path,
                'components': components,
                'total_percentage': total,
                'extraction_method': 'OpenAI GPT-4o'
            }, f, indent=2, ensure_ascii=False)
        print(f'\n💾 Resultados guardados en: {output_file}')
    else:
        print('\n⚠️  No se encontraron componentes')
        print('\nRespuesta completa de OpenAI:')
        print(json.dumps(result, indent=2))
        
else:
    print('\n❌ No se encontró sección 3 de composición en el PDF')

print('\n' + '='*80)













