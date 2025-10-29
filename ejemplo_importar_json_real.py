#!/usr/bin/env python3
"""
Ejemplo de Importación de Cuestionario JSON Real

Este script demuestra cómo importar cuestionarios en formato JSON
con la estructura real de Lluch (fieldCode, fieldName, fieldType, value).

Uso:
    python ejemplo_importar_json_real.py
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.database import SessionLocal
from app.parsers.questionnaire_json_parser import QuestionnaireJSONParser
from app.models.questionnaire import Questionnaire
from app.models.material import Material


def analyze_json_structure():
    """Analyze the structure of the real JSON file"""
    print("\n" + "="*80)
    print("  🔍 ANALYZING REAL JSON STRUCTURE")
    print("="*80 + "\n")
    
    json_file = "data/questionnaires/JSON Z1_Basicilo_MPE.txt"
    
    if not os.path.exists(json_file):
        print(f"❌ File not found: {json_file}")
        return
    
    parser = QuestionnaireJSONParser(json_file)
    data = parser.parse()
    
    print(f"📋 REQUEST ID: {data['request_id']}")
    print(f"📊 TOTAL FIELDS: {len(data['fields'])}")
    print(f"📝 RESPONSES: {len(data['responses'])} (excluding blank fields)")
    
    print(f"\n📈 FIELD TYPES DISTRIBUTION:")
    for field_type, count in sorted(data['metadata']['field_types'].items(), key=lambda x: -x[1]):
        print(f"   • {field_type}: {count}")
    
    print(f"\n🔑 EXTRACTED METADATA:")
    if 'supplier_name' in data['metadata']:
        print(f"   • Supplier: {data['metadata']['supplier_name']}")
    if 'product_name' in data['metadata']:
        print(f"   • Product: {data['metadata']['product_name']}")
    if 'product_code' in data['metadata']:
        print(f"   • Product Code: {data['metadata']['product_code']}")
    
    print(f"\n📄 SAMPLE FIELDS:")
    sample_count = 0
    for field in data['fields'][:10]:
        if field.get('fieldType') != 'blank':
            print(f"\n   {field.get('fieldCode')}: {field.get('fieldName')}")
            print(f"      Type: {field.get('fieldType')}")
            print(f"      Value: {field.get('value')[:80]}..." if len(str(field.get('value', ''))) > 80 else f"      Value: {field.get('value')}")
            sample_count += 1
            if sample_count >= 5:
                break
    
    print(f"\n✅ Analysis completed!\n")
    
    return data


def show_sections():
    """Show fields organized by sections"""
    print("\n" + "="*80)
    print("  📑 FIELDS ORGANIZED BY SECTIONS")
    print("="*80 + "\n")
    
    json_file = "data/questionnaires/JSON Z1_Basicilo_MPE.txt"
    
    if not os.path.exists(json_file):
        print(f"❌ File not found: {json_file}")
        return
    
    parser = QuestionnaireJSONParser(json_file)
    sections = parser.extract_by_section()
    
    print(f"Found {len(sections)} sections:\n")
    
    for section_name, fields in sorted(sections.items()):
        print(f"📂 {section_name}: {len(fields)} fields")
        
        # Show first 3 fields of each section
        for i, field in enumerate(fields[:3]):
            if field.get('fieldType') != 'blank':
                print(f"   • {field.get('fieldCode')}: {field.get('fieldName')[:60]}")
        
        if len(fields) > 3:
            print(f"   ... and {len(fields) - 3} more")
        print()


def show_critical_fields():
    """Show critical fields extracted"""
    print("\n" + "="*80)
    print("  ⭐ CRITICAL FIELDS FOR BLUE LINE COMPARISON")
    print("="*80 + "\n")
    
    json_file = "data/questionnaires/JSON Z1_Basicilo_MPE.txt"
    
    if not os.path.exists(json_file):
        print(f"❌ File not found: {json_file}")
        return
    
    parser = QuestionnaireJSONParser(json_file)
    critical = parser.get_critical_fields()
    
    for key, field_data in critical.items():
        print(f"📌 {key}:")
        print(f"   Code: {field_data['field_code']}")
        print(f"   Name: {field_data['field_name']}")
        print(f"   Value: {field_data['value']}")
        print()


def demo_import():
    """Demonstrate importing the JSON to database"""
    print("\n" + "="*80)
    print("  💾 IMPORT JSON TO DATABASE")
    print("="*80 + "\n")
    
    json_file = "data/questionnaires/JSON Z1_Basicilo_MPE.txt"
    
    if not os.path.exists(json_file):
        print(f"❌ File not found: {json_file}")
        return
    
    db = SessionLocal()
    try:
        # First, ensure material exists
        print("▶ Checking for material BASIL0003...")
        
        material = db.query(Material).filter(
            Material.reference_code == "BASIL0003"
        ).first()
        
        if not material:
            print("⚠️  Material BASIL0003 not found. Creating...")
            material = Material(
                reference_code="BASIL0003",
                name="H.E. BASILIC INDES",
                supplier="M.P.E MATIERES PREMIERES ESSENTIELL",
                supplier_code="MPE-001",
                description="Basil essential oil from India",
                cas_number="8015-73-4",
                material_type="essential_oil",
                is_active=True,
                sap_status="Z1",
                is_blue_line_eligible=True
            )
            db.add(material)
            db.commit()
            db.refresh(material)
            print(f"✅ Created material: {material.reference_code}")
        else:
            print(f"✅ Found material: {material.reference_code}")
        
        # Import questionnaire
        print(f"\n▶ Importing questionnaire from JSON...")
        questionnaire_id = QuestionnaireJSONParser.import_from_json(
            json_file,
            db,
            material_code="BASIL0003"
        )
        
        questionnaire = db.query(Questionnaire).filter(
            Questionnaire.id == questionnaire_id
        ).first()
        
        print(f"\n✅ Questionnaire imported successfully!")
        print(f"\n📊 DETAILS:")
        print(f"   • ID: {questionnaire.id}")
        print(f"   • Material: {material.reference_code} - {material.name}")
        print(f"   • Supplier: {questionnaire.supplier_code}")
        print(f"   • Type: {questionnaire.questionnaire_type.value}")
        print(f"   • Version: {questionnaire.version}")
        print(f"   • Status: {questionnaire.status.value}")
        print(f"   • Total fields: {len(questionnaire.responses)}")
        print(f"   • Request ID: {questionnaire.responses.get('_request_id')}")
        
        print(f"\n📱 View in UI:")
        print(f"   http://localhost:5173/questionnaires/{questionnaire.id}")
        
        print(f"\n💡 Next steps:")
        print(f"   1. Submit questionnaire for review")
        print(f"   2. System will automatically validate against Blue Line")
        print(f"   3. AI will analyze and generate risk score")
        print(f"   4. Critical deviations will create incidents")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()
    
    print()


def convert_to_csv():
    """Convert JSON to CSV for easier viewing"""
    print("\n" + "="*80)
    print("  📄 CONVERT JSON TO CSV")
    print("="*80 + "\n")
    
    json_file = "data/questionnaires/JSON Z1_Basicilo_MPE.txt"
    csv_file = "data/questionnaires/BASIL0003_exported.csv"
    
    if not os.path.exists(json_file):
        print(f"❌ File not found: {json_file}")
        return
    
    parser = QuestionnaireJSONParser(json_file)
    parser.convert_to_csv(csv_file)
    
    print(f"✅ Converted to CSV: {csv_file}")
    print(f"   You can now open it in Excel/LibreOffice for easier viewing")
    print()


def main():
    """Main demo function"""
    print("\n🚀" + "="*78 + "🚀")
    print("  REAL QUESTIONNAIRE JSON IMPORT - DEMONSTRATION")
    print("  Lluch Format: fieldCode + fieldName + fieldType + value")
    print("🚀" + "="*78 + "🚀")
    
    # Step 1: Analyze structure
    analyze_json_structure()
    
    # Step 2: Show sections
    show_sections()
    
    # Step 3: Show critical fields
    show_critical_fields()
    
    # Step 4: Convert to CSV (optional, for viewing)
    convert_to_csv()
    
    # Step 5: Import to database (uncomment to actually import)
    print("\n" + "="*80)
    print("  To import to database, uncomment the line below in the script:")
    print("  demo_import()")
    print("="*80 + "\n")
    
    # Uncomment to import:
    # demo_import()


if __name__ == "__main__":
    main()

