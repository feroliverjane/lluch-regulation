"""
Create Questionnaire Template from Real JSON

Extracts all fields from the real Lluch JSON and creates a reusable template
with the exact structure, questions, and field types.
"""

import sys
import os
import json
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.core.database import SessionLocal
from app.models.questionnaire_template import QuestionnaireTemplate, TemplateType
from app.parsers.questionnaire_json_parser import QuestionnaireJSONParser


def extract_section_number(field_code: str) -> int:
    """Extract section number from fieldCode (e.g., q3t1s2f15 -> 2)"""
    try:
        if 's' in field_code and 'f' in field_code:
            return int(field_code.split('s')[1].split('f')[0])
        return 0
    except:
        return 0


def extract_tab_number(field_code: str) -> int:
    """Extract tab number from fieldCode (e.g., q3t1s2f15 -> 1)"""
    try:
        if 't' in field_code and 's' in field_code:
            return int(field_code.split('t')[1].split('s')[0])
        return 0
    except:
        return 0


def organize_by_sections(fields: list) -> dict:
    """Organize fields by tab and section"""
    organized = defaultdict(lambda: defaultdict(list))
    
    for field in fields:
        field_code = field.get("fieldCode", "")
        field_type = field.get("fieldType", "")
        
        # Skip blank fields
        if field_type == "blank" or not field.get("fieldName", "").strip():
            continue
        
        tab = extract_tab_number(field_code)
        section = extract_section_number(field_code)
        
        organized[tab][section].append(field)
    
    return organized


def determine_field_requirements(field: dict) -> dict:
    """Determine if a field is required and its validation rules"""
    field_name = field.get("fieldName", "").lower()
    field_type = field.get("fieldType", "")
    
    # Critical fields that should be required
    critical_keywords = [
        "supplier name", "product name", "product code", "cas", "einecs",
        "kosher", "halal", "food grade", "natural", "pure",
        "country", "botanical name", "reach", "certificate"
    ]
    
    is_critical = any(keyword in field_name for keyword in critical_keywords)
    
    # Determine if required based on field type and criticality
    required = False
    if field_type in ["inputText", "lov", "selectManyMenu"] and is_critical:
        required = True
    
    return {
        "required": required,
        "critical": is_critical,
        "validation_rules": get_validation_rules(field_type)
    }


def get_validation_rules(field_type: str) -> dict:
    """Get validation rules based on field type"""
    rules = {
        "inputText": {"type": "string", "minLength": 1, "maxLength": 500},
        "inputNumber": {"type": "number", "min": 0},
        "inputTextarea": {"type": "string", "minLength": 1, "maxLength": 5000},
        "yesNoNA": {"type": "enum", "values": ["YES", "NO", "NA"]},
        "yesNoComments": {"type": "compound", "primary": "yesNo", "secondary": "text"},
        "checkComents": {"type": "boolean"},
        "lov": {"type": "list_of_values"},
        "selectManyMenu": {"type": "multi_select"},
        "selectManyCheckbox": {"type": "multi_select_checkbox"},
        "checkTableMatCasPercen": {"type": "table", "columns": ["material", "cas", "percentage"]},
        "tableDescYesNoPercen": {"type": "table", "columns": ["description", "yes_no", "percentage"]},
        "tableDescYesNoSubtCASPercent": {"type": "table", "columns": ["description", "yes_no", "substance", "cas", "percentage"]},
        "presenceIngredientTablePercentHandlers2": {"type": "complex_table"},
        "checkTableMatCasAnnexPercen": {"type": "table", "columns": ["material", "cas", "annex", "percentage"]},
        "checkTableMatStatusCFRPercen": {"type": "table", "columns": ["material", "status", "cfr", "percentage"]},
        "checkTableMatCasROPercen": {"type": "table", "columns": ["material", "cas", "ro", "percentage"]},
    }
    
    return rules.get(field_type, {"type": "string"})


def create_template_from_json(db: SessionLocal):
    """Create template from real JSON file"""
    print("\n" + "="*80)
    print("  📋 CREATING QUESTIONNAIRE TEMPLATE FROM REAL JSON")
    print("="*80 + "\n")
    
    # Path to JSON
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
    json_file = os.path.join(project_root, "data", "questionnaires", "JSON Z1_Basicilo_MPE.txt")
    section_names_file = os.path.join(project_root, "data", "questionnaires", "section_names_mapping.json")
    tab_names_file = os.path.join(project_root, "data", "questionnaires", "tab_names_mapping.json")
    
    print(f"▶ Reading: {os.path.basename(json_file)}")
    
    # Load section names mapping if it exists
    section_names = {}
    if os.path.exists(section_names_file):
        with open(section_names_file, 'r', encoding='utf-8') as f:
            section_names = json.load(f)
        print(f"✅ Loaded section names mapping: {len(section_names)} sections")
    else:
        print(f"⚠️  Section names mapping not found, using numeric names")
    
    # Load tab names mapping if it exists
    tab_names = {}
    if os.path.exists(tab_names_file):
        with open(tab_names_file, 'r', encoding='utf-8') as f:
            tab_names = json.load(f)
        print(f"✅ Loaded tab names mapping: {len(tab_names)} tabs")
    else:
        print(f"⚠️  Tab names mapping not found, using numeric names")
    
    # Parse JSON
    parser = QuestionnaireJSONParser(json_file)
    data = parser.parse()
    
    print(f"✅ Parsed {len(data['fields'])} total fields")
    print(f"   ({len(data['responses'])} non-blank fields)\n")
    
    # Organize by sections
    organized = organize_by_sections(data['fields'])
    
    total_tabs = len(organized)
    total_sections = sum(len(sections) for sections in organized.values())
    
    print(f"📊 Structure:")
    print(f"   • Tabs: {total_tabs}")
    print(f"   • Sections: {total_sections}")
    print(f"   • Fields: {len(data['responses'])}")
    
    # Build questions schema
    questions_schema = []
    field_count = 0
    
    print(f"\n▶ Building questions schema...")
    
    for tab in sorted(organized.keys()):
        for section in sorted(organized[tab].keys()):
            fields = organized[tab][section]
            
            for field in fields:
                requirements = determine_field_requirements(field)
                
                question = {
                    "fieldCode": field.get("fieldCode"),
                    "fieldName": field.get("fieldName"),
                    "fieldType": field.get("fieldType"),
                    "tab": tab,
                    "section": section,
                    "required": requirements["required"],
                    "critical": requirements["critical"],
                    "validationRules": requirements["validation_rules"],
                    "defaultValue": field.get("value", "") if field.get("value") not in ["[]", ""] else None,
                    "order": field_count
                }
                
                questions_schema.append(question)
                field_count += 1
    
    print(f"✅ Created schema with {len(questions_schema)} questions")
    
    # Show distribution
    print(f"\n📈 Field Type Distribution:")
    field_type_count = defaultdict(int)
    for q in questions_schema:
        field_type_count[q["fieldType"]] += 1
    
    for ft, count in sorted(field_type_count.items(), key=lambda x: -x[1])[:10]:
        print(f"   • {ft}: {count}")
    
    # Create template in database
    print(f"\n▶ Saving template to database...")
    
    # Check if template already exists
    existing = db.query(QuestionnaireTemplate).filter(
        QuestionnaireTemplate.name == "Lluch Standard Homologation Template"
    ).first()
    
    if existing:
        print(f"⚠️  Template already exists (ID: {existing.id}), updating...")
        existing.questions_schema = questions_schema
        existing.total_questions = len(questions_schema)
        existing.total_sections = total_sections
        existing.section_names = section_names
        existing.tab_names = tab_names
        existing.version = "1.0"
        db.commit()
        template = existing
    else:
        template = QuestionnaireTemplate(
            name="Lluch Standard Homologation Template",
            description="Complete homologation questionnaire template based on real Lluch format. Includes 174 fields covering supplier info, certifications, compliance, allergens, quality parameters, and sustainability.",
            template_type=TemplateType.INITIAL_HOMOLOGATION,
            version="1.0",
            questions_schema=questions_schema,
            total_questions=len(questions_schema),
            total_sections=total_sections,
            section_names=section_names,
            tab_names=tab_names,
            is_active=True,
            is_default=True
        )
        
        db.add(template)
        db.commit()
        db.refresh(template)
    
    print(f"✅ Template saved!")
    print(f"\n📋 TEMPLATE DETAILS:")
    print(f"   • ID: {template.id}")
    print(f"   • Name: {template.name}")
    print(f"   • Type: {template.template_type.value}")
    print(f"   • Version: {template.version}")
    print(f"   • Total Questions: {template.total_questions}")
    print(f"   • Total Sections: {template.total_sections}")
    
    # Show sample questions from different sections
    print(f"\n📝 Sample Questions:")
    sample_tabs = [1, 3, 4, 6, 8]
    for tab in sample_tabs:
        tab_questions = [q for q in questions_schema if q["tab"] == tab][:2]
        if tab_questions:
            print(f"\n   Tab {tab}:")
            for q in tab_questions:
                print(f"      • [{q['fieldCode']}] {q['fieldName'][:60]}")
                print(f"        Type: {q['fieldType']}, Required: {q['required']}")
    
    print(f"\n✅ Template creation complete!")
    print(f"\nThis template can now be used to:")
    print(f"  1. Render dynamic forms in frontend")
    print(f"  2. Validate questionnaire completeness")
    print(f"  3. Export to different formats (PDF, Excel)")
    print(f"  4. Create variations for different material types")
    print()
    
    return template


def export_template_to_json(template: QuestionnaireTemplate, output_file: str):
    """Export template to JSON file for documentation"""
    template_export = {
        "id": template.id,
        "name": template.name,
        "description": template.description,
        "type": template.template_type.value,
        "version": template.version,
        "total_questions": template.total_questions,
        "total_sections": template.total_sections,
        "questions": template.questions_schema
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(template_export, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Exported template to: {output_file}")


def main():
    """Main execution"""
    print("\n🚀" + "="*78 + "🚀")
    print("  QUESTIONNAIRE TEMPLATE GENERATOR")
    print("  Extract Structure from Real Lluch JSON")
    print("🚀" + "="*78 + "🚀")
    
    db = SessionLocal()
    try:
        template = create_template_from_json(db)
        
        # Export to file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
        export_file = os.path.join(project_root, "data", "questionnaires", "template_lluch_standard.json")
        
        export_template_to_json(template, export_file)
        
        print("\n" + "="*80)
        print("  ✅ TEMPLATE READY")
        print("="*80)
        print(f"\nAccess template:")
        print(f"  • Database ID: {template.id}")
        print(f"  • Export file: {export_file}")
        print(f"  • API: http://localhost:8000/api/questionnaire-templates/{template.id}")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()

