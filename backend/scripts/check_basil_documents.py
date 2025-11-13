#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para revisar qué documentos están cargados para el composite del basílico
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.material import Material
from app.models.blue_line import BlueLine
import json

# Use production database or test database
DB_URL = settings.DATABASE_URL
print(f"📁 Conectando a base de datos: {DB_URL}")

engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

def check_basil_documents():
    """Revisar documentos cargados para el composite del basílico"""
    db = SessionLocal()
    
    try:
        # Buscar el material BASIL0003
        material = db.query(Material).filter(
            Material.reference_code == "BASIL0003"
        ).first()
        
        if not material:
            print("❌ Material BASIL0003 no encontrado en la base de datos")
            return
        
        print("=" * 80)
        print(f"  📄 DOCUMENTOS PARA COMPOSITE DE BASIL0003")
        print("=" * 80)
        print(f"\n✅ Material encontrado:")
        print(f"   - Código: {material.reference_code}")
        print(f"   - Nombre: {material.name}")
        print(f"   - ID: {material.id}")
        
        # Buscar Blue Line para este material
        blue_line = db.query(BlueLine).filter(
            BlueLine.material_id == material.id
        ).first()
        
        if not blue_line:
            print(f"\n⚠️  No se encontró Blue Line para BASIL0003")
            return
        
        print(f"\n📋 Blue Line encontrada:")
        print(f"   - ID: {blue_line.id}")
        print(f"   - Material ID: {blue_line.material_id}")
        
        # Revisar calculation_metadata para documentos pendientes
        if blue_line.calculation_metadata:
            print(f"\n📊 Metadata de cálculo:")
            metadata = blue_line.calculation_metadata
            
            if isinstance(metadata, dict):
                pending_docs = metadata.get("pending_documents", [])
                
                if pending_docs:
                    print(f"\n📄 Documentos pendientes de extracción: {len(pending_docs)}")
                    print("-" * 80)
                    
                    for idx, doc in enumerate(pending_docs, 1):
                        print(f"\n🔹 Documento #{idx}")
                        print(f"   - Nombre: {doc.get('filename', 'N/A')}")
                        print(f"   - Ruta: {doc.get('path', 'N/A')}")
                        print(f"   - Tipo: {doc.get('type', 'N/A')}")
                        print(f"   - Fecha de carga: {doc.get('upload_date', 'N/A')}")
                        
                        # Verificar si el archivo existe
                        doc_path = Path(doc.get('path', ''))
                        if doc_path.exists():
                            file_size = doc_path.stat().st_size / 1024  # KB
                            print(f"   - Estado: ✅ Existe ({file_size:.2f} KB)")
                            
                            # Mostrar ruta completa
                            print(f"   - Ruta completa: {doc_path.resolve()}")
                        else:
                            print(f"   - Estado: ❌ No encontrado en disco")
                            print(f"   - Ruta buscada: {doc_path}")
                else:
                    print(f"\n⚠️  No hay documentos pendientes en calculation_metadata")
                
                # Mostrar otros campos de metadata
                print(f"\n📋 Otros campos en metadata:")
                for key, value in metadata.items():
                    if key != "pending_documents":
                        print(f"   - {key}: {value}")
            else:
                print(f"\n⚠️  calculation_metadata no es un diccionario: {type(metadata)}")
                print(f"   Contenido: {metadata}")
        else:
            print(f"\n⚠️  No hay calculation_metadata en la Blue Line")
        
        # También revisar si hay composite y sus source_documents
        if blue_line.composite_id:
            from app.models.composite import Composite
            composite = db.query(Composite).filter(Composite.id == blue_line.composite_id).first()
            
            if composite:
                print(f"\n🧪 Composite asociado:")
                print(f"   - ID: {composite.id}")
                print(f"   - Tipo: {composite.composite_type.value if composite.composite_type else 'N/A'}")
                
                if composite.source_documents:
                    print(f"\n📄 Documentos fuente del composite:")
                    source_docs = composite.source_documents
                    if isinstance(source_docs, list):
                        for idx, doc in enumerate(source_docs, 1):
                            print(f"\n   {idx}. {doc.get('filename', 'N/A')}")
                            print(f"      - Ruta: {doc.get('path', 'N/A')}")
                            print(f"      - Tipo: {doc.get('type', 'N/A')}")
                            print(f"      - Fecha: {doc.get('upload_date', 'N/A')}")
                    else:
                        print(f"   Formato: {type(source_docs)}")
                        print(f"   Contenido: {json.dumps(source_docs, indent=4, ensure_ascii=False)}")
                else:
                    print(f"   ⚠️  No hay source_documents en el composite")
        
    except Exception as e:
        print(f"\n❌ Error al consultar: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_basil_documents()


