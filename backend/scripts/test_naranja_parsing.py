#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar el parsing del JSON de naranja y ver qué código detecta
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.parsers.questionnaire_json_parser import QuestionnaireJSONParser

def test_naranja_parsing():
    """Probar el parsing del JSON de naranja"""
    json_path = Path(__file__).parent.parent.parent / "data" / "questionnaires" / "rehomologacion_naranja_con_mismatches.json"
    
    if not json_path.exists():
        print(f"❌ Archivo no encontrado: {json_path}")
        return
    
    print(f"📄 Analizando: {json_path.name}\n")
    
    parser = QuestionnaireJSONParser(str(json_path))
    parsed_data = parser.parse()
    
    metadata = parsed_data.get("metadata", {})
    responses = parsed_data.get("responses", {})
    
    print("=" * 60)
    print("METADATA EXTRAÍDA:")
    print("=" * 60)
    print(f"  product_code: {metadata.get('product_code', 'NO ENCONTRADO')}")
    print(f"  product_name: {metadata.get('product_name', 'NO ENCONTRADO')}")
    print(f"  supplier_name: {metadata.get('supplier_name', 'NO ENCONTRADO')}")
    
    print("\n" + "=" * 60)
    print("CAMPOS RELEVANTES EN EL JSON:")
    print("=" * 60)
    
    # Buscar campos relacionados con código de producto
    relevant_fields = [
        "q3t1s2f15",  # Supplier Name
        "q3t1s2f16",  # Product Name
        "q3t1s2f17",  # Supplier´s product code
    ]
    
    for field_code in relevant_fields:
        if field_code in responses:
            field_data = responses[field_code]
            print(f"\n  {field_code}:")
            print(f"    Nombre: {field_data.get('name', 'N/A')}")
            print(f"    Valor: {field_data.get('value', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("ANÁLISIS:")
    print("=" * 60)
    
    product_code = metadata.get("product_code", "")
    product_name = metadata.get("product_name", "")
    
    if product_code:
        print(f"✅ Código detectado: '{product_code}'")
    else:
        print("❌ NO se detectó código de producto en metadata")
        print("   Buscando en responses...")
        
        # Buscar manualmente
        supplier_product_code_field = responses.get("q3t1s2f17")
        if supplier_product_code_field:
            detected_code = supplier_product_code_field.get("value", "")
            print(f"   Código encontrado en q3t1s2f17: '{detected_code}'")
            
            if detected_code == "OLA001":
                print("\n✅ El código OLA001 está en el JSON")
                print("   El sistema debería detectarlo correctamente")
            else:
                print(f"\n⚠️  El código en el JSON es '{detected_code}', no 'OLA001'")
        else:
            print("   ❌ No se encontró el campo q3t1s2f17 (Supplier´s product code)")
    
    if product_name:
        print(f"\n✅ Nombre de producto detectado: '{product_name}'")
        # Verificar si tiene formato [CODE]
        if product_name.startswith("[") and "]" in product_name:
            code_from_name = product_name.split("]")[0].replace("[", "")
            print(f"   Código extraído del nombre: '{code_from_name}'")
        else:
            print("   El nombre no tiene formato [CODE]")

if __name__ == "__main__":
    test_naranja_parsing()










