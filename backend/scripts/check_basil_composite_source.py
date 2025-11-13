#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para revisar qué archivos se usaron para actualizar el composite Z1 de BASIL0003
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.material import Material
from app.models.composite import Composite, CompositeType
import json

# Use production database or test database
DB_URL = settings.DATABASE_URL
print(f"📁 Conectando a base de datos: {DB_URL}")

engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

def check_basil_composite_source():
    """Revisar qué archivos se usaron para el composite Z1 de BASIL0003"""
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
        print(f"  📋 COMPOSITE Z1 PARA BASIL0003")
        print("=" * 80)
        print(f"\n✅ Material encontrado:")
        print(f"   - Código: {material.reference_code}")
        print(f"   - Nombre: {material.name}")
        print(f"   - ID: {material.id}")
        
        # Buscar composites Z1 para este material
        composites = db.query(Composite).filter(
            Composite.material_id == material.id,
            Composite.composite_type == CompositeType.Z1
        ).order_by(Composite.created_at.desc()).all()
        
        if not composites:
            print(f"\n⚠️  No se encontraron composites Z1 para BASIL0003")
            return
        
        print(f"\n📦 Composites Z1 encontrados: {len(composites)}")
        print("-" * 80)
        
        for idx, composite in enumerate(composites, 1):
            print(f"\n🔹 Composite #{idx} (ID: {composite.id})")
            print(f"   - Versión: {composite.version}")
            print(f"   - Estado: {composite.status.value}")
            print(f"   - Origen: {composite.origin.value}")
            print(f"   - Confianza de extracción: {composite.extraction_confidence}%" if composite.extraction_confidence else "   - Confianza: N/A")
            print(f"   - Creado: {composite.created_at}")
            
            # Mostrar documentos fuente
            if composite.source_documents:
                print(f"\n   📄 Documentos fuente utilizados:")
                if isinstance(composite.source_documents, list):
                    for doc_idx, doc in enumerate(composite.source_documents, 1):
                        print(f"      {doc_idx}. {doc.get('filename', 'N/A')}")
                        print(f"         - Ruta: {doc.get('path', 'N/A')}")
                        print(f"         - Tipo: {doc.get('type', 'N/A')}")
                        print(f"         - Fecha de carga: {doc.get('upload_date', 'N/A')}")
                        
                        # Verificar si el archivo existe
                        doc_path = Path(doc.get('path', ''))
                        if doc_path.exists():
                            file_size = doc_path.stat().st_size / 1024  # KB
                            print(f"         - Estado: ✅ Existe ({file_size:.2f} KB)")
                        else:
                            print(f"         - Estado: ❌ No encontrado en disco")
                else:
                    print(f"      Formato: {type(composite.source_documents)}")
                    print(f"      Contenido: {json.dumps(composite.source_documents, indent=6, ensure_ascii=False)}")
            else:
                print(f"\n   ⚠️  No hay documentos fuente registrados")
            
            # Mostrar metadata
            if composite.composite_metadata:
                print(f"\n   📊 Metadata de extracción:")
                metadata = composite.composite_metadata
                if isinstance(metadata, dict):
                    print(f"      - Método: {metadata.get('extraction_method', 'N/A')}")
                    print(f"      - Fecha de extracción: {metadata.get('extraction_date', 'N/A')}")
                    print(f"      - Cuestionario origen: {metadata.get('source_questionnaire', 'N/A')}")
                else:
                    print(f"      {json.dumps(metadata, indent=6, ensure_ascii=False)}")
            
            # Mostrar componentes extraídos
            if composite.components:
                print(f"\n   🧪 Componentes extraídos ({len(composite.components)}):")
                for comp in composite.components:
                    print(f"      - {comp.component_name}: {comp.percentage}%")
                    if comp.cas_number:
                        print(f"        CAS: {comp.cas_number}")
            
            # Mostrar notas
            if composite.notes:
                print(f"\n   📝 Notas:")
                print(f"      {composite.notes}")
            
            print("-" * 80)
        
    except Exception as e:
        print(f"\n❌ Error al consultar: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_basil_composite_source()


