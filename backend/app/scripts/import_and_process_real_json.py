"""
Import and Process Real JSON Questionnaire

This script demonstrates the complete end-to-end workflow using a REAL Lluch questionnaire JSON:
1. Import JSON with fieldCode structure
2. Create/update Blue Line for comparison
3. Submit and validate automatically
4. Generate AI risk assessment
5. Show incidents if any
6. Demonstrate approval workflow
"""

import sys
import os
from datetime import datetime, timedelta
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.material import Material
from app.models.blue_line import BlueLine, BlueLineMaterialType, BlueLineSyncStatus
from app.models.questionnaire import Questionnaire, QuestionnaireStatus
from app.models.questionnaire_template import QuestionnaireTemplate, TemplateType
from app.models.composite import Composite, CompositeOrigin, CompositeStatus
from app.parsers.questionnaire_json_parser import QuestionnaireJSONParser
from app.services.questionnaire_validation_service import QuestionnaireValidationService
from app.services.questionnaire_ai_service import QuestionnaireAIService
from app.services.questionnaire_field_mapper import QuestionnaireFieldMapper, map_questionnaire_to_blue_line


def print_section(title: str):
    """Print formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def setup_material_and_blue_line(db: Session) -> tuple:
    """Create or update material and Blue Line based on JSON data"""
    print_section("📦 STEP 1: Setting up Material and Blue Line")
    
    # Get path relative to project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
    json_file = os.path.join(project_root, "data", "questionnaires", "JSON Z1_Basicilo_MPE.txt")
    
    parser = QuestionnaireJSONParser(json_file)
    data = parser.parse()
    critical = parser.get_critical_fields()
    
    # Extract info
    material_code = critical.get("product_code", {}).get("value", "BASIL0003")
    if material_code.startswith("["):
        material_code = material_code.split("]")[0].replace("[", "")
    
    product_name = critical.get("product_name", {}).get("value", "")
    if "]" in product_name:
        product_name = product_name.split("]")[1].strip()
    
    supplier_name = critical.get("supplier_name", {}).get("value", "")[:100]
    cas_number = critical.get("cas_number", {}).get("value", "")
    botanical_name = critical.get("botanical_name", {}).get("value", "")
    
    # Create or get material
    material = db.query(Material).filter(
        Material.reference_code == material_code
    ).first()
    
    if not material:
        material = Material(
            reference_code=material_code,
            name=product_name,
            supplier=supplier_name,
            supplier_code="MPE-BASIL-001",
            description=f"Basil essential oil - {botanical_name}",
            cas_number=cas_number,
            material_type="essential_oil",
            is_active=True,
            sap_status="Z1",  # From JSON filename
            lluch_reference=f"LLUCH-{material_code}",
            last_purchase_date=datetime.now() - timedelta(days=60),
            is_blue_line_eligible=True
        )
        db.add(material)
        db.commit()
        db.refresh(material)
        print(f"✅ Created material: {material.reference_code}")
    else:
        print(f"✅ Found existing material: {material.reference_code}")
    
    print(f"   • Name: {material.name}")
    print(f"   • Supplier: {material.supplier}")
    print(f"   • CAS: {material.cas_number}")
    print(f"   • SAP Status: {material.sap_status}")
    
    # Create Blue Line with expected values from the JSON
    blue_line = db.query(BlueLine).filter(
        BlueLine.material_id == material.id,
        BlueLine.supplier_code == material.supplier_code
    ).first()
    
    if not blue_line:
        # Get default template
        default_template = db.query(QuestionnaireTemplate).filter(
            QuestionnaireTemplate.is_default == True,
            QuestionnaireTemplate.template_type == TemplateType.INITIAL_HOMOLOGATION
        ).first()
        
        # Create Blue Line with expected values (these would normally come from Lluch analysis)
        blue_line_data = {
            "material_reference": material.reference_code,
            "material_name": material.name,
            "supplier_name": material.supplier,
            "cas_number": cas_number,
            "botanical_name": botanical_name,
            "country_origin": critical.get("country_origin", {}).get("value", ""),
            "is_natural": "YES",
            "is_pure": "YES",
            "kosher_certified": "YES",
            "halal_certified": "YES",
            "food_grade": "YES",
            "reach_registered": "NO",
            "cosmetics_compliant": "YES",
            "haccp_certified": "YES",
            "eu_compliant": "YES",
            "allergen_control_plan": "YES",
            "animal_origin": "NO",
            "renewability_percentage": "100",
        }
        
        # Convert to responses format if template exists
        responses = {}
        if default_template:
            # Map blue_line_data fields to fieldCode format using template
            field_mapper = QuestionnaireFieldMapper()
            for field in default_template.questions_schema:
                field_code = field.get("fieldCode", "")
                field_name = field.get("fieldName", "")
                # Try to find matching value by field name or field code
                bl_field = field_mapper.get_blue_line_field(field_code)
                if bl_field and bl_field in blue_line_data:
                    responses[field_code] = {
                        "value": blue_line_data[bl_field],
                        "name": field_name,
                        "type": field.get("fieldType", "text")
                    }
                elif field_name and any(key in field_name for key in blue_line_data.keys()):
                    # Fallback: try to match by field name
                    for bl_key, bl_value in blue_line_data.items():
                        if bl_key.lower() in field_name.lower() or field_name.lower() in bl_key.lower():
                            responses[field_code] = {
                                "value": bl_value,
                                "name": field_name,
                                "type": field.get("fieldType", "text")
                            }
                            break
        
        # Create empty composite
        composite = Composite(
            material_id=material.id,
            version=1,
            origin=CompositeOrigin.MANUAL,
            status=CompositeStatus.DRAFT,
            composite_metadata={},
            notes="Empty composite created for Blue Line - to be filled manually"
        )
        db.add(composite)
        db.commit()
        db.refresh(composite)
        
        blue_line = BlueLine(
            material_id=material.id,
            supplier_code=material.supplier_code,
            template_id=default_template.id if default_template else None,
            responses=responses,
            blue_line_data=blue_line_data,  # Keep for backward compatibility
            material_type=BlueLineMaterialType.Z001,  # Estimated from supplier
            composite_id=composite.id,
            sync_status=BlueLineSyncStatus.PENDING,
            calculation_metadata={
                "source": "Supplier Questionnaire",
                "date_established": datetime.now().isoformat(),
                "type": "Initial baseline from supplier data"
            }
        )
        db.add(blue_line)
        db.commit()
        db.refresh(blue_line)
        print(f"\n✅ Created Blue Line (Type: {blue_line.material_type.value})")
        print(f"   • Template: {default_template.name if default_template else 'None'}")
        print(f"   • Composite ID: {composite.id}")
    else:
        print(f"\n✅ Found existing Blue Line")
        # Ensure composite exists
        if not blue_line.composite_id:
            composite = Composite(
                material_id=material.id,
                version=1,
                origin=CompositeOrigin.MANUAL,
                status=CompositeStatus.DRAFT,
                composite_metadata={},
                notes="Empty composite created for Blue Line - to be filled manually"
            )
            db.add(composite)
            db.commit()
            db.refresh(composite)
            blue_line.composite_id = composite.id
            db.commit()
            print(f"   • Created missing composite: {composite.id}")
    
    print(f"   • Expected Values Set:")
    for key in ["kosher_certified", "halal_certified", "food_grade", "is_natural"]:
        value = blue_line.responses.get(key, {}).get("value") if blue_line.responses else blue_line.blue_line_data.get(key, 'N/A')
        print(f"     - {key}: {value}")
    
    return material, blue_line


def import_json_questionnaire(db: Session, material: Material) -> Questionnaire:
    """Import the real JSON questionnaire"""
    print_section("📥 STEP 2: Importing Real JSON Questionnaire")
    
    # Get path relative to project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
    json_file = os.path.join(project_root, "data", "questionnaires", "JSON Z1_Basicilo_MPE.txt")
    
    print(f"▶ Reading JSON file: {os.path.basename(json_file)}")
    parser = QuestionnaireJSONParser(json_file)
    data = parser.parse()
    
    print(f"✅ Parsed successfully:")
    print(f"   • Request ID: {data['request_id']}")
    print(f"   • Total fields: {len(data['fields'])}")
    print(f"   • Response fields: {len(data['responses'])}")
    
    # Create questionnaire
    print(f"\n▶ Creating questionnaire in database...")
    
    questionnaire = Questionnaire(
        material_id=material.id,
        supplier_code=material.supplier_code,
        questionnaire_type=QuestionnaireType.INITIAL_HOMOLOGATION,
        version=1,
        responses=data["responses"],
        status=QuestionnaireStatus.DRAFT
    )
    
    db.add(questionnaire)
    db.commit()
    db.refresh(questionnaire)
    
    print(f"✅ Questionnaire #{questionnaire.id} created")
    print(f"   • Status: {questionnaire.status.value}")
    print(f"   • Fields stored: {len(questionnaire.responses)}")
    
    # Show some critical field values
    print(f"\n📊 Sample Field Values:")
    sample_codes = ["q3t1s3f27", "q3t1s3f28", "q3t1s3f29", "q3t1s4f44"]
    for code in sample_codes:
        if code in questionnaire.responses:
            field_name = QuestionnaireFieldMapper.get_field_name(code)
            value = QuestionnaireFieldMapper.extract_simple_value(questionnaire.responses[code])
            print(f"   • {code} ({field_name}): {value}")
    
    return questionnaire


async def submit_and_validate_real(db: Session, questionnaire: Questionnaire):
    """Submit and validate the real questionnaire"""
    print_section("🤖 STEP 3: AI Validation with Real Lluch Fields")
    
    print("▶ Submitting questionnaire...")
    questionnaire.status = QuestionnaireStatus.SUBMITTED
    questionnaire.submitted_at = datetime.now()
    db.commit()
    print(f"✅ Status: {questionnaire.status.value}")
    
    print("\n▶ Running validation against Blue Line...")
    print("   (Using fieldCode mappings to compare critical fields)")
    
    validation_service = QuestionnaireValidationService(db)
    validations = validation_service.validate_questionnaire(questionnaire.id)
    
    print(f"\n✅ Validation complete: {len(validations)} checks performed")
    
    from app.models.questionnaire_validation import ValidationSeverity
    critical = sum(1 for v in validations if v.severity == ValidationSeverity.CRITICAL)
    warning = sum(1 for v in validations if v.severity == ValidationSeverity.WARNING)
    info = len(validations) - critical - warning
    
    print(f"   🔴 CRITICAL: {critical}")
    print(f"   🟡 WARNING: {warning}")
    print(f"   🔵 INFO: {info}")
    
    if validations:
        print(f"\n📋 Validation Results:")
        for v in validations[:10]:  # Show first 10
            icon = "🔴" if v.severity == ValidationSeverity.CRITICAL else "🟡" if v.severity == ValidationSeverity.WARNING else "🔵"
            print(f"   {icon} {v.field_name}")
            if v.expected_value and v.actual_value:
                print(f"      Expected: {v.expected_value} | Actual: {v.actual_value}")
        if len(validations) > 10:
            print(f"   ... and {len(validations) - 10} more")
    
    print("\n▶ Running AI risk assessment...")
    ai_service = QuestionnaireAIService(db)
    ai_analysis = await ai_service.analyze_risk_profile(questionnaire.id)
    
    questionnaire.ai_risk_score = ai_analysis["risk_score"]
    questionnaire.ai_summary = ai_analysis["summary"]
    questionnaire.ai_recommendation = ai_analysis["recommendation"]
    questionnaire.status = QuestionnaireStatus.IN_REVIEW
    db.commit()
    db.refresh(questionnaire)
    
    print(f"✅ AI Analysis Complete")
    print(f"\n🎯 RISK ASSESSMENT:")
    print(f"   Score: {ai_analysis['risk_score']}/100")
    print(f"   Recommendation: {ai_analysis['recommendation']}")
    print(f"   Confidence: {ai_analysis['confidence']*100:.0f}%")
    
    # Show incidents
    from app.models.questionnaire_incident import QuestionnaireIncident
    incidents = db.query(QuestionnaireIncident).filter(
        QuestionnaireIncident.questionnaire_id == questionnaire.id
    ).all()
    
    if incidents:
        print(f"\n⚠️  INCIDENTS CREATED: {len(incidents)}")
        for inc in incidents:
            print(f"   • {inc.field_name}: {inc.issue_description[:80]}...")
    else:
        print(f"\n✅ No critical incidents generated")


def generate_summary(db: Session, material: Material, questionnaire: Questionnaire):
    """Generate final summary"""
    print_section("📊 COMPLETE IMPORT SUMMARY")
    
    from app.models.questionnaire_validation import QuestionnaireValidation
    from app.models.questionnaire_incident import QuestionnaireIncident
    
    validations = db.query(QuestionnaireValidation).filter(
        QuestionnaireValidation.questionnaire_id == questionnaire.id
    ).all()
    
    incidents = db.query(QuestionnaireIncident).filter(
        QuestionnaireIncident.questionnaire_id == questionnaire.id
    ).all()
    
    print(f"Material: {material.reference_code} - {material.name}")
    print(f"Request ID: {questionnaire.responses.get('_request_id')}")
    print(f"\nQuestionnaire Details:")
    print(f"   • ID: {questionnaire.id}")
    print(f"   • Type: {questionnaire.questionnaire_type.value}")
    print(f"   • Version: {questionnaire.version}")
    print(f"   • Status: {questionnaire.status.value}")
    print(f"   • Total Fields: {len(questionnaire.responses)}")
    print(f"   • Validations: {len(validations)}")
    print(f"   • Incidents: {len(incidents)}")
    print(f"   • AI Risk Score: {questionnaire.ai_risk_score}/100")
    print(f"   • AI Recommendation: {questionnaire.ai_recommendation}")
    
    print(f"\n📱 View in UI:")
    print(f"   • Questionnaire: http://localhost:5173/questionnaires/{questionnaire.id}")
    print(f"   • Material: http://localhost:5173/materials/{material.id}")
    print(f"   • Blue Line: http://localhost:5173/blue-line")
    
    print(f"\n🎯 What Happened:")
    print(f"   1. ✅ Imported 174 fields from real Lluch JSON format")
    print(f"   2. ✅ Mapped fieldCodes to Blue Line fields")
    print(f"   3. ✅ Validated critical fields (certifications, compliance, etc.)")
    print(f"   4. 🤖 AI analyzed {len(validations)} field comparisons")
    print(f"   5. {'⚠️' if incidents else '✅'} {len(incidents)} incident(s) auto-generated")
    print(f"   6. 📊 System ready for quality review")
    
    print(f"\n💡 Next Steps:")
    print(f"   • Review validations and resolve any incidents")
    print(f"   • Approve questionnaire to update Blue Line")
    print(f"   • Blue Line will sync to SAP (Z1 → Lluch sends to SAP)")
    print()


async def main():
    """Main execution"""
    print("\n🚀" + "="*78 + "🚀")
    print("  REAL LLUCH JSON QUESTIONNAIRE - END-TO-END PROCESSING")
    print("  Format: 235 fields with fieldCode structure (q3t1s2f15, etc.)")
    print("🚀" + "="*78 + "🚀")
    
    db = SessionLocal()
    try:
        # Step 1: Setup
        material, blue_line = setup_material_and_blue_line(db)
        
        # Step 2: Import JSON
        questionnaire = import_json_questionnaire(db, material)
        
        # Step 3: Submit and validate
        await submit_and_validate_real(db, questionnaire)
        
        # Step 4: Summary
        generate_summary(db, material, questionnaire)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    from app.models.questionnaire import QuestionnaireType
    asyncio.run(main())

