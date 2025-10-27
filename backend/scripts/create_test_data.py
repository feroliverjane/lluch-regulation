#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para crear datos de prueba: analisis cromatograficos y composites
"""

import requests
import json
import os
import sys

# Configuración
API_BASE = "http://localhost:8000/api"
UPLOADS_DIR = "../data/uploads"

def upload_analysis(material_id, csv_file, batch_number, supplier):
    """Subir analisis cromatografico"""
    url = f"{API_BASE}/chromatographic-analyses"
    
    with open(csv_file, 'rb') as f:
        files = {'file': f}
        data = {
            'material_id': material_id,
            'batch_number': batch_number,
            'supplier': supplier,
            'weight': '1.0'
        }
        
        try:
            response = requests.post(url, files=files, data=data)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Analisis subido: {result.get('filename', 'N/A')} (ID: {result.get('id', 'N/A')})")
                return result.get('id')
            else:
                print(f"❌ Error subiendo analisis: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error subiendo analisis: {e}")
            return None

def calculate_composite(material_id, origin="LAB", notes=""):
    """Calcular composite"""
    url = f"{API_BASE}/composites/calculate"
    
    data = {
        'material_id': material_id,
        'origin': origin,
        'notes': notes
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Composite calculado: ID {result.get('id', 'N/A')}, Versión {result.get('version', 'N/A')}")
            return result.get('id')
        else:
            print(f"❌ Error calculando composite: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error calculando composite: {e}")
        return None

def submit_for_approval(composite_id):
    """Enviar composite para aprobacion"""
    url = f"{API_BASE}/composites/{composite_id}/submit-for-approval"
    
    try:
        response = requests.put(url)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Composite enviado para aprobacion: ID {composite_id}")
            return True
        else:
            print(f"❌ Error enviando para aprobacion: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error enviando para aprobacion: {e}")
        return False

def main():
    print("🚀 Creando datos de prueba para composites PENDING_APPROVAL...")
    
    # Datos de materiales disponibles
    materials = [
        {"id": 1, "name": "Lemon Oil Italy", "reference": "LEM-001"},
        {"id": 3, "name": "Lavender Oil France", "reference": "LAV-003"},
        {"id": 4, "name": "Peppermint Oil USA", "reference": "PEP-004"},
    ]
    
    # Archivos CSV de análisis
    analysis_files = [
        {"material_id": 1, "file": "lemon_analysis.csv", "batch": "LEM-2024-001", "supplier": "Citrus Italy SpA"},
        {"material_id": 3, "file": "lavender_analysis.csv", "batch": "LAV-2024-001", "supplier": "Provence Essences"},
        {"material_id": 4, "file": "peppermint_analysis.csv", "batch": "PEP-2024-001", "supplier": "American Mint Co"},
    ]
    
    composite_ids = []
    
    # 1. Subir analisis
    print("\n📊 Subiendo analisis cromatograficos...")
    for analysis in analysis_files:
        file_path = os.path.join(UPLOADS_DIR, analysis["file"])
        if os.path.exists(file_path):
            analysis_id = upload_analysis(
                analysis["material_id"],
                file_path,
                analysis["batch"],
                analysis["supplier"]
            )
        else:
            print(f"⚠️  Archivo no encontrado: {file_path}")
    
    # 2. Calcular composites
    print("\n🧮 Calculando composites...")
    for material in materials:
        composite_id = calculate_composite(
            material["id"],
            origin="LAB",
            notes=f"Composite de prueba para {material['name']}"
        )
        if composite_id:
            composite_ids.append(composite_id)
    
    # 3. Enviar composites para aprobacion
    print("\n📋 Enviando composites para aprobacion...")
    for composite_id in composite_ids:
        submit_for_approval(composite_id)
    
    print(f"\n✅ Proceso completado! Se crearon {len(composite_ids)} composites para aprobacion.")
    print("Ahora puedes ver los composites en estado PENDING_APPROVAL en la pagina de Aprobaciones.")

if __name__ == "__main__":
    main()
