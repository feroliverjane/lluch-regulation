#!/usr/bin/env python3
"""
Ejemplo de Importación de Cuestionarios desde CSV

Este script demuestra cómo importar cuestionarios de proveedores
desde archivos CSV al sistema.

Uso:
    python ejemplo_importar_cuestionario.py
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.database import SessionLocal
from app.parsers.questionnaire_csv_parser import QuestionnaireCSVParser
from app.models.questionnaire import Questionnaire


def demo_parse_csv():
    """Demonstrate CSV parsing without importing to DB"""
    print("\n" + "="*80)
    print("  📄 DEMO: Parsing Questionnaire CSV")
    print("="*80 + "\n")
    
    csv_file = "data/questionnaires/DEMO-MAT-001_v2_rehomologation.csv"
    
    if not os.path.exists(csv_file):
        print(f"❌ File not found: {csv_file}")
        return
    
    parser = QuestionnaireCSVParser(csv_file)
    data = parser.parse()
    
    print("📋 METADATA:")
    for key, value in data["metadata"].items():
        print(f"   • {key}: {value}")
    
    print(f"\n📝 RESPONSES: {len(data['responses'])} campos")
    print("\n   Ejemplos de respuestas:")
    sample_fields = [
        "company_name", "purity_percentage", "moisture_content", 
        "sustainability_score", "allergen_declaration"
    ]
    for field in sample_fields:
        if field in data["responses"]:
            print(f"   • {field}: {data['responses'][field]}")
    
    if data.get("changes_explanation"):
        print(f"\n⚠️  EXPLICACIONES DE CAMBIOS: {len(data['changes_explanation'])}")
        for change in data["changes_explanation"][:3]:
            print(f"\n   • {change['field']}:")
            print(f"     Explicación: {change['explanation'][:80]}...")
    
    print("\n✅ Parsing completed successfully!\n")


def demo_import_to_database():
    """Demonstrate importing CSV to database"""
    print("\n" + "="*80)
    print("  💾 DEMO: Importing Questionnaire to Database")
    print("="*80 + "\n")
    
    csv_file = "data/questionnaires/DEMO-MAT-001_v1_initial_homologation.csv"
    
    if not os.path.exists(csv_file):
        print(f"❌ File not found: {csv_file}")
        return
    
    db = SessionLocal()
    try:
        # Import
        print(f"▶ Importing: {csv_file}")
        questionnaire_id = QuestionnaireCSVParser.import_from_csv(csv_file, db)
        
        # Retrieve and display
        questionnaire = db.query(Questionnaire).filter(
            Questionnaire.id == questionnaire_id
        ).first()
        
        print(f"\n✅ Questionnaire imported successfully!")
        print(f"\n📊 DETAILS:")
        print(f"   • ID: {questionnaire.id}")
        print(f"   • Material ID: {questionnaire.material_id}")
        print(f"   • Supplier: {questionnaire.supplier_code}")
        print(f"   • Type: {questionnaire.questionnaire_type.value}")
        print(f"   • Version: {questionnaire.version}")
        print(f"   • Status: {questionnaire.status.value}")
        print(f"   • Response fields: {len(questionnaire.responses)}")
        
        print(f"\n📱 View in UI:")
        print(f"   http://localhost:5173/questionnaires/{questionnaire.id}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
    finally:
        db.close()
    
    print()


def show_file_structure():
    """Show the structure of CSV questionnaire files"""
    print("\n" + "="*80)
    print("  📁 ESTRUCTURA DE ARCHIVOS CSV DISPONIBLES")
    print("="*80 + "\n")
    
    questionnaire_dir = "data/questionnaires"
    
    if not os.path.exists(questionnaire_dir):
        print(f"❌ Directory not found: {questionnaire_dir}")
        return
    
    files = [f for f in os.listdir(questionnaire_dir) if f.endswith('.csv')]
    
    if not files:
        print("⚠️  No CSV files found")
        return
    
    print(f"Found {len(files)} questionnaire CSV file(s):\n")
    
    for file in sorted(files):
        file_path = os.path.join(questionnaire_dir, file)
        size = os.path.getsize(file_path)
        
        print(f"📄 {file}")
        print(f"   Size: {size:,} bytes")
        print(f"   Path: {file_path}")
        
        # Try to extract basic info
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[:10]:
                    if line.startswith('Material,'):
                        material = line.split(',')[1].strip()
                        print(f"   Material: {material}")
                    elif line.startswith('Versión,'):
                        version = line.split(',')[1].strip()
                        print(f"   Version: v{version}")
        except:
            pass
        
        print()


def main():
    """Main demo function"""
    print("\n🚀" + "="*78 + "🚀")
    print("  QUESTIONNAIRE CSV IMPORT - DEMONSTRATION")
    print("  Supplier Document → Automated System Workflow")
    print("🚀" + "="*78 + "🚀")
    
    # Show available files
    show_file_structure()
    
    # Demo 1: Parse CSV (view contents)
    demo_parse_csv()
    
    # Demo 2: Import to database
    # Uncomment to actually import:
    # demo_import_to_database()
    
    print("="*80)
    print("  ✅ DEMO COMPLETE")
    print("="*80)
    print("\nThese CSV files simulate real supplier submissions.")
    print("They can be:")
    print("  1. Parsed to extract data")
    print("  2. Imported directly to the database")
    print("  3. Validated automatically against Blue Line")
    print("  4. Analyzed by AI for risk assessment")
    print("\nTo import a CSV:")
    print("  from app.parsers.questionnaire_csv_parser import QuestionnaireCSVParser")
    print("  questionnaire_id = QuestionnaireCSVParser.import_from_csv('file.csv', db)")
    print()


if __name__ == "__main__":
    main()

