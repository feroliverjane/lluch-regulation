#!/usr/bin/env python3
"""
Script de ejemplo para subir análisis CSV y calcular composites
Lluch Regulation

Ejecutar: python3 ejemplo_subir_csv.py
"""

import urllib.request
import json
import os
from pathlib import Path


API_URL = "http://localhost:8000/api"
DATA_DIR = Path(__file__).parent / "data" / "uploads"


def subir_analisis_csv(material_id: int, archivo_csv: str, batch_number: str, supplier: str):
    """Subir un archivo CSV de análisis cromatográfico"""
    
    archivo_path = DATA_DIR / archivo_csv
    
    if not archivo_path.exists():
        print(f"❌ Archivo no encontrado: {archivo_path}")
        return None
    
    print(f"\n📤 Subiendo: {archivo_csv}")
    print(f"   Material ID: {material_id}")
    print(f"   Lote: {batch_number}")
    print(f"   Proveedor: {supplier}")
    
    # Leer el archivo
    with open(archivo_path, 'rb') as f:
        contenido = f.read()
    
    # Crear multipart form data manualmente
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    
    # Construir el cuerpo de la petición
    body = []
    
    # Campo: material_id
    body.append(f'--{boundary}')
    body.append('Content-Disposition: form-data; name="material_id"')
    body.append('')
    body.append(str(material_id))
    
    # Campo: batch_number
    body.append(f'--{boundary}')
    body.append('Content-Disposition: form-data; name="batch_number"')
    body.append('')
    body.append(batch_number)
    
    # Campo: supplier
    body.append(f'--{boundary}')
    body.append('Content-Disposition: form-data; name="supplier"')
    body.append('')
    body.append(supplier)
    
    # Campo: weight
    body.append(f'--{boundary}')
    body.append('Content-Disposition: form-data; name="weight"')
    body.append('')
    body.append('1.0')
    
    # Campo: file
    body.append(f'--{boundary}')
    body.append(f'Content-Disposition: form-data; name="file"; filename="{archivo_csv}"')
    body.append('Content-Type: text/csv')
    body.append('')
    body.append(contenido.decode('utf-8'))
    
    body.append(f'--{boundary}--')
    body.append('')
    
    body_bytes = '\r\n'.join(body).encode('utf-8')
    
    # Hacer la petición
    req = urllib.request.Request(
        f"{API_URL}/chromatographic-analyses",
        data=body_bytes,
        headers={
            'Content-Type': f'multipart/form-data; boundary={boundary}'
        }
    )
    
    try:
        response = urllib.request.urlopen(req)
        resultado = json.loads(response.read())
        
        print(f"   ✅ Análisis subido con ID: {resultado['id']}")
        print(f"   Componentes encontrados: {len(resultado['parsed_data']['components'])}")
        print(f"   Estado: {'✅ Procesado' if resultado['is_processed'] == 1 else '❌ Error'}")
        
        if resultado['parsed_data'].get('validation_errors'):
            print(f"   ⚠️  Warnings: {resultado['parsed_data']['validation_errors']}")
        
        # Mostrar primeros componentes
        print(f"\n   📊 Componentes detectados:")
        for comp in resultado['parsed_data']['components'][:5]:
            print(f"      • {comp['component_name']}: {comp['percentage']}%")
        
        if len(resultado['parsed_data']['components']) > 5:
            print(f"      ... y {len(resultado['parsed_data']['components']) - 5} más")
        
        return resultado
        
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode()
        print(f"   ❌ Error: {e.code}")
        print(f"   {error_msg}")
        return None


def calcular_composite(material_id: int, analysis_ids: list = None):
    """Calcular composite a partir de los análisis"""
    
    print(f"\n🧮 Calculando composite para material {material_id}...")
    
    datos = {
        "material_id": material_id,
        "origin": "LAB",
        "notes": "Composite calculado automáticamente desde análisis CSV"
    }
    
    if analysis_ids:
        datos["analysis_ids"] = analysis_ids
    
    req = urllib.request.Request(
        f"{API_URL}/composites/calculate",
        data=json.dumps(datos).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        response = urllib.request.urlopen(req)
        composite = json.loads(response.read())
        
        print(f"   ✅ Composite calculado!")
        print(f"   ID: {composite['id']}")
        print(f"   Versión: {composite['version']}")
        print(f"   Componentes: {len(composite['components'])}")
        print(f"   Estado: {composite['status']}")
        
        print(f"\n   📊 Composición final:")
        for comp in sorted(composite['components'], key=lambda x: x['percentage'], reverse=True)[:10]:
            print(f"      • {comp['component_name']}: {comp['percentage']:.2f}%")
            if comp['confidence_level']:
                print(f"        Confianza: {comp['confidence_level']:.1f}%")
        
        return composite
        
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode()
        print(f"   ❌ Error: {e.code}")
        print(f"   {error_msg}")
        return None


def ejemplo_completo():
    """Ejemplo completo: subir varios CSVs y calcular composite"""
    
    print("="*70)
    print("   EJEMPLO: SUBIR CSV Y CALCULAR COMPOSITE")
    print("="*70)
    
    # Material 1: Lemon Oil
    print("\n📦 Trabajando con material: Lemon Oil Italy (ID: 1)")
    
    # Subir análisis
    analisis1 = subir_analisis_csv(
        material_id=1,
        archivo_csv="lemon_oil_batch_A2023.csv",
        batch_number="A2023",
        supplier="Citrus Italy SpA"
    )
    
    if not analisis1:
        print("\n❌ Error al subir el análisis")
        return
    
    # Calcular composite
    composite = calcular_composite(
        material_id=1,
        analysis_ids=[analisis1['id']]
    )
    
    if composite:
        print("\n" + "="*70)
        print("✅ PROCESO COMPLETADO EXITOSAMENTE")
        print("="*70)
        print(f"\n🔗 Ver en la interfaz:")
        print(f"   Material: http://localhost:5173/materials/1")
        print(f"   Composite: http://localhost:5173/composites/{composite['id']}")
        print(f"\n📚 Ver en la API:")
        print(f"   Análisis: {API_URL}/chromatographic-analyses/{analisis1['id']}")
        print(f"   Composite: {API_URL}/composites/{composite['id']}")


def main():
    """Función principal"""
    
    print("\n" + "="*70)
    print("   EJEMPLOS DE ANÁLISIS CROMATOGRÁFICOS")
    print("="*70)
    
    print("\n📁 Archivos CSV disponibles:")
    archivos = [
        "lemon_oil_batch_A2023.csv",
        "orange_oil_batch_B2024.csv",
        "lavender_oil_provence_2024.csv",
        "peppermint_oil_usa_2024.csv",
        "eucalyptus_oil_australia_2024.csv"
    ]
    
    for i, archivo in enumerate(archivos, 1):
        archivo_path = DATA_DIR / archivo
        if archivo_path.exists():
            print(f"   {i}. ✅ {archivo}")
        else:
            print(f"   {i}. ❌ {archivo} (no encontrado)")
    
    print("\n" + "="*70)
    
    # Ejecutar ejemplo completo
    ejemplo_completo()
    
    print("\n💡 Próximos pasos:")
    print("   • Sube más archivos CSV desde la interfaz web")
    print("   • Compara diferentes versiones de composites")
    print("   • Usa la API para crear flujos automáticos")


if __name__ == "__main__":
    main()






