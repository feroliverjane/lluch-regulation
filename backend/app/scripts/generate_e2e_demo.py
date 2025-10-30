"""
End-to-End Demo Data Generator

This script creates a complete workflow demonstration showing:
1. Initial homologation questionnaire (approved)
2. New rehomologation with deviations
3. Automatic AI validation and risk assessment
4. Incident creation and resolution
5. Approval workflow with Blue Line update

Run this to see the complete automated system in action!
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.material import Material
from app.models.blue_line import BlueLine, BlueLineMaterialType, BlueLineSyncStatus
from app.models.questionnaire_template import QuestionnaireTemplate, TemplateType
from app.models.composite import Composite, CompositeOrigin, CompositeStatus
from app.models.questionnaire import Questionnaire, QuestionnaireType, QuestionnaireStatus
from app.models.questionnaire_validation import QuestionnaireValidation, ValidationType, ValidationSeverity
from app.models.questionnaire_incident import QuestionnaireIncident, IncidentStatus, ResolutionAction
from app.services.questionnaire_validation_service import QuestionnaireValidationService
from app.services.questionnaire_ai_service import QuestionnaireAIService


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def clear_demo_data(db: Session):
    """Clear existing demo data"""
    print_section("🗑️  STEP 0: Cleaning Previous Demo Data")
    
    db.query(QuestionnaireIncident).delete()
    db.query(QuestionnaireValidation).delete()
    db.query(Questionnaire).delete()
    db.commit()
    
    print("✅ Cleared all questionnaire data")


def create_initial_scenario(db: Session) -> tuple:
    """Create the initial scenario with material and Blue Line"""
    print_section("📦 STEP 1: Creating Initial Scenario")
    
    # Get or create a material
    material = db.query(Material).filter(Material.reference_code == "DEMO-MAT-001").first()
    
    if not material:
        material = Material(
            reference_code="DEMO-MAT-001",
            name="Premium Lavender Essential Oil",
            supplier="Provence Natural Extracts",
            supplier_code="PROV-LAV-2024",
            description="High-quality lavender essential oil from Provence, France",
            cas_number="8000-28-0",
            material_type="essential_oil",
            is_active=True,
            sap_status="Z2",
            lluch_reference="LLUCH-103721",
            last_purchase_date=datetime.now() - timedelta(days=90),
            is_blue_line_eligible=True
        )
        db.add(material)
        db.commit()
        db.refresh(material)
        print(f"✅ Created material: {material.reference_code} - {material.name}")
    else:
        print(f"✅ Using existing material: {material.reference_code}")
    
    # Create Blue Line with expected values
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
        
        blue_line_data = {
            "material_reference": material.reference_code,
            "material_name": material.name,
            "supplier_name": material.supplier,
            "quality_certificate": "ISO 9001:2015",
            "purity_percentage": "99.8",
            "moisture_content": "0.15",
            "sustainability_score": "85",
            "organic_certified": "Yes",
            "allergen_declaration": "None",
            "country_of_origin": "France",
            "expected_standard": "EU Regulation Compliant"
        }
        
        # Convert to responses format if template exists
        responses = {}
        if default_template:
            from app.services.questionnaire_field_mapper import QuestionnaireFieldMapper
            field_mapper = QuestionnaireFieldMapper()
            for field in default_template.questions_schema:
                field_code = field.get("fieldCode", "")
                field_name = field.get("fieldName", "")
                bl_field = field_mapper.get_blue_line_field(field_code)
                if bl_field and bl_field in blue_line_data:
                    responses[field_code] = {
                        "value": blue_line_data[bl_field],
                        "name": field_name,
                        "type": field.get("fieldType", "text")
                    }
        
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
            material_type=BlueLineMaterialType.Z002,
            composite_id=composite.id,
            sync_status=BlueLineSyncStatus.SYNCED,
            calculation_metadata={
                "source": "Lluch Laboratory Analysis",
                "last_analysis_date": "2024-06-15",
                "analyst": "Dr. María García"
            }
        )
        db.add(blue_line)
        db.commit()
        db.refresh(blue_line)
        print(f"✅ Created Blue Line for {material.reference_code}")
        print(f"   - Material Type: {blue_line.material_type.value}")
        print(f"   - Template: {default_template.name if default_template else 'None'}")
        print(f"   - Composite ID: {composite.id}")
        print(f"   - Expected Purity: {blue_line.blue_line_data['purity_percentage']}%")
        print(f"   - Expected Moisture: {blue_line.blue_line_data['moisture_content']}%")
        print(f"   - Sustainability Score: {blue_line.blue_line_data['sustainability_score']}")
    else:
        print(f"✅ Using existing Blue Line")
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
    
    return material, blue_line


def create_initial_questionnaire(db: Session, material: Material) -> Questionnaire:
    """Create initial approved questionnaire (v1)"""
    print_section("📋 STEP 2: Creating Initial Questionnaire (v1) - APPROVED")
    
    # This represents the questionnaire that was approved 6 months ago
    q1 = Questionnaire(
        material_id=material.id,
        supplier_code=material.supplier_code,
        questionnaire_type=QuestionnaireType.INITIAL_HOMOLOGATION,
        version=1,
        responses={
            # Company Info
            "company_name": "Provence Natural Extracts SAS",
            "contact_person": "Jean-Pierre Dubois",
            "contact_email": "jp.dubois@provence-extracts.fr",
            "contact_phone": "+33 4 90 12 34 56",
            
            # Certifications
            "quality_certificate": "ISO 9001:2015",
            "organic_certified": "Yes",
            "kosher_certified": "No",
            "halal_certified": "No",
            "fair_trade_certified": "Yes",
            
            # Sustainability
            "sustainable_sourcing": "Yes",
            "carbon_neutral": "In Progress",
            "endangered_species_used": "No",
            "sustainability_score": 85,
            
            # Allergens
            "allergen_declaration": "None",
            "gluten_free": "Yes",
            "lactose_free": "Yes",
            
            # Quality Parameters (Matching Blue Line)
            "purity_percentage": "99.8",
            "moisture_content": "0.15",
            "ash_content": "0.05",
            "heavy_metals_compliant": "Yes",
            "microbiological_compliant": "Yes",
            
            # Supply Chain
            "country_of_origin": "France",
            "manufacturing_site": "Lavender Fields Production Facility, Provence",
            "batch_tracking_available": "Yes",
            "shelf_life_months": "24",
            
            # Documentation
            "technical_data_sheet_available": "Yes",
            "safety_data_sheet_available": "Yes",
            "coa_provided": "Yes",
            
            # Additional
            "gmo_free": "Yes",
            "irradiation_used": "No",
            "additional_comments": "Premium grade lavender oil. Harvested during optimal season."
        },
        status=QuestionnaireStatus.APPROVED,
        ai_risk_score=12,
        ai_summary=(
            "✅ Excellent initial submission. All quality parameters meet or exceed requirements. "
            "Strong certifications including organic and fair trade. "
            "No concerns identified. Material demonstrates high quality standards."
        ),
        ai_recommendation="APPROVE",
        created_at=datetime.now() - timedelta(days=180),
        submitted_at=datetime.now() - timedelta(days=179),
        reviewed_at=datetime.now() - timedelta(days=178),
        approved_at=datetime.now() - timedelta(days=178)
    )
    
    db.add(q1)
    db.commit()
    db.refresh(q1)
    
    print(f"✅ Created Initial Questionnaire #{q1.id}")
    print(f"   - Status: {q1.status.value}")
    print(f"   - AI Risk Score: {q1.ai_risk_score}/100 (LOW RISK)")
    print(f"   - Approved: {q1.approved_at.strftime('%Y-%m-%d')}")
    print(f"   - Key Values:")
    print(f"     • Purity: {q1.responses['purity_percentage']}%")
    print(f"     • Moisture: {q1.responses['moisture_content']}%")
    print(f"     • Sustainability: {q1.responses['sustainability_score']}")
    
    return q1


def create_rehomologation_with_deviations(db: Session, material: Material, previous_q: Questionnaire) -> Questionnaire:
    """Create rehomologation questionnaire with concerning deviations"""
    print_section("🔄 STEP 3: Creating Rehomologation Questionnaire (v2) - WITH DEVIATIONS")
    
    # This questionnaire has some concerning changes
    q2 = Questionnaire(
        material_id=material.id,
        supplier_code=material.supplier_code,
        questionnaire_type=QuestionnaireType.REHOMOLOGATION,
        version=2,
        previous_version_id=previous_q.id,
        responses={
            # Company Info (same)
            "company_name": "Provence Natural Extracts SAS",
            "contact_person": "Jean-Pierre Dubois",
            "contact_email": "jp.dubois@provence-extracts.fr",
            "contact_phone": "+33 4 90 12 34 56",
            
            # Certifications (some changes)
            "quality_certificate": "ISO 9001:2015",
            "organic_certified": "Yes",
            "kosher_certified": "No",
            "halal_certified": "No",
            "fair_trade_certified": "No",  # ❌ CHANGED: Lost certification
            
            # Sustainability (degraded)
            "sustainable_sourcing": "Partial",  # ❌ CHANGED: Downgraded
            "carbon_neutral": "No",  # ❌ CHANGED: Was "In Progress"
            "endangered_species_used": "No",
            "sustainability_score": 62,  # ❌ CRITICAL: Dropped from 85 to 62
            
            # Allergens (new concern)
            "allergen_declaration": "May contain traces of tree nuts",  # ❌ CHANGED: New allergen
            "gluten_free": "Yes",
            "lactose_free": "Yes",
            
            # Quality Parameters (CONCERNING CHANGES)
            "purity_percentage": "97.2",  # ❌ CRITICAL: Dropped from 99.8% to 97.2%
            "moisture_content": "0.85",  # ❌ CRITICAL: Increased from 0.15% to 0.85%
            "ash_content": "0.12",  # ❌ WARNING: Increased from 0.05% to 0.12%
            "heavy_metals_compliant": "Yes",
            "microbiological_compliant": "Yes",
            
            # Supply Chain
            "country_of_origin": "France",
            "manufacturing_site": "Lavender Fields Production Facility, Provence",
            "batch_tracking_available": "Yes",
            "shelf_life_months": "18",  # ❌ CHANGED: Reduced from 24 to 18 months
            
            # Documentation
            "technical_data_sheet_available": "Yes",
            "safety_data_sheet_available": "Yes",
            "coa_provided": "Yes",
            
            # Additional
            "gmo_free": "Yes",
            "irradiation_used": "No",
            "additional_comments": "Recent crop variations due to climate conditions. Working on quality improvements."
        },
        status=QuestionnaireStatus.DRAFT,
        created_at=datetime.now() - timedelta(days=3)
    )
    
    db.add(q2)
    db.commit()
    db.refresh(q2)
    
    print(f"✅ Created Rehomologation Questionnaire #{q2.id}")
    print(f"   - Status: {q2.status.value}")
    print(f"   - Links to previous version: #{previous_q.id}")
    print(f"\n⚠️  DETECTED CHANGES (vs v1 and Blue Line):")
    print(f"   • Purity: 99.8% → 97.2% (📉 -2.6%, CRITICAL)")
    print(f"   • Moisture: 0.15% → 0.85% (📈 +467%, CRITICAL)")
    print(f"   • Sustainability: 85 → 62 (📉 -27%, CRITICAL)")
    print(f"   • Allergen: None → Tree nuts (NEW CONCERN)")
    print(f"   • Fair Trade: Yes → No (CERTIFICATION LOST)")
    print(f"   • Shelf Life: 24 → 18 months (-25%)")
    
    return q2


async def submit_and_validate(db: Session, questionnaire: Questionnaire):
    """Submit questionnaire and run automatic validation with AI"""
    print_section("🤖 STEP 4: Submitting for Review - AI AUTOMATIC VALIDATION")
    
    print("▶ Submitting questionnaire...")
    questionnaire.status = QuestionnaireStatus.SUBMITTED
    questionnaire.submitted_at = datetime.now()
    db.commit()
    print(f"✅ Status changed: DRAFT → SUBMITTED")
    
    print("\n▶ Running automatic validation against Blue Line...")
    validation_service = QuestionnaireValidationService(db)
    validations = validation_service.validate_questionnaire(questionnaire.id)
    print(f"✅ Generated {len(validations)} validation checks")
    
    # Show validation results
    print("\n📊 VALIDATION RESULTS:")
    critical_count = sum(1 for v in validations if v.severity == ValidationSeverity.CRITICAL)
    warning_count = sum(1 for v in validations if v.severity == ValidationSeverity.WARNING)
    
    print(f"   🔴 CRITICAL: {critical_count}")
    print(f"   🟡 WARNING: {warning_count}")
    print(f"   🔵 INFO: {len(validations) - critical_count - warning_count}")
    
    for v in validations:
        icon = "🔴" if v.severity == ValidationSeverity.CRITICAL else "🟡" if v.severity == ValidationSeverity.WARNING else "🔵"
        print(f"\n   {icon} {v.severity.value}: {v.field_name}")
        print(f"      Expected: {v.expected_value} | Actual: {v.actual_value}")
        if v.deviation_percentage:
            print(f"      Deviation: {v.deviation_percentage:.1f}%")
        print(f"      {v.message}")
    
    print("\n▶ Running AI Risk Assessment...")
    ai_service = QuestionnaireAIService(db)
    ai_analysis = await ai_service.analyze_risk_profile(questionnaire.id)
    
    questionnaire.ai_risk_score = ai_analysis["risk_score"]
    questionnaire.ai_summary = ai_analysis["summary"]
    questionnaire.ai_recommendation = ai_analysis["recommendation"]
    questionnaire.status = QuestionnaireStatus.IN_REVIEW
    db.commit()
    db.refresh(questionnaire)
    
    print(f"✅ AI Analysis Complete")
    print(f"\n🎯 AI RISK ASSESSMENT:")
    print(f"   Score: {ai_analysis['risk_score']}/100", end="")
    if ai_analysis['risk_score'] >= 70:
        print(" (🔴 HIGH RISK)")
    elif ai_analysis['risk_score'] >= 40:
        print(" (🟡 MEDIUM RISK)")
    else:
        print(" (🟢 LOW RISK)")
    
    print(f"   Recommendation: {ai_analysis['recommendation']}")
    print(f"   Confidence: {ai_analysis['confidence']*100:.0f}%")
    print(f"\n   Summary:")
    for line in ai_analysis['summary'].split('. '):
        if line.strip():
            print(f"   • {line.strip()}")
    
    # Show incidents
    incidents = db.query(QuestionnaireIncident).filter(
        QuestionnaireIncident.questionnaire_id == questionnaire.id
    ).all()
    
    if incidents:
        print(f"\n⚠️  AUTO-GENERATED INCIDENTS: {len(incidents)}")
        for inc in incidents:
            print(f"   • Incident #{inc.id}: {inc.field_name}")
            print(f"     Status: {inc.status.value}")
            print(f"     {inc.issue_description}")


def demonstrate_incident_resolution(db: Session, questionnaire: Questionnaire):
    """Show incident resolution workflow"""
    print_section("🔧 STEP 5: Incident Resolution Workflow")
    
    incidents = db.query(QuestionnaireIncident).filter(
        QuestionnaireIncident.questionnaire_id == questionnaire.id,
        QuestionnaireIncident.status == IncidentStatus.OPEN
    ).all()
    
    if not incidents:
        print("✅ No open incidents to resolve")
        return
    
    print(f"Found {len(incidents)} open incidents that need resolution\n")
    
    # Demonstrate different resolution paths
    for i, incident in enumerate(incidents, 1):
        print(f"Incident #{incident.id}: {incident.field_name}")
        print(f"  Issue: {incident.issue_description}")
        
        if i == 1:
            # Override first incident
            print(f"  ✅ Action: USER OVERRIDE")
            print(f"  Justification: 'The deviation in {incident.field_name} is due to seasonal ")
            print(f"                  variations in raw material. Supplier has provided documentation ")
            print(f"                  confirming this is temporary and next batch will return to normal.")
            print(f"                  Quality team has reviewed and accepts this variance.'")
            
            incident.status = IncidentStatus.OVERRIDDEN
            incident.resolution_action = ResolutionAction.USER_OVERRIDE
            incident.override_justification = (
                f"The deviation in {incident.field_name} is due to seasonal variations in raw material. "
                "Supplier has provided documentation confirming this is temporary and next batch will "
                "return to normal. Quality team has reviewed and accepts this variance."
            )
            incident.resolved_at = datetime.now()
        else:
            # Escalate others
            print(f"  📤 Action: ESCALATED TO SUPPLIER")
            print(f"  Note: Requesting supplier investigation and corrective action plan")
            
            incident.status = IncidentStatus.ESCALATED_TO_SUPPLIER
            incident.resolution_action = ResolutionAction.ESCALATED
            incident.supplier_notified_at = datetime.now()
            incident.resolution_notes = "Requesting supplier investigation and corrective action plan"
        
        print()
    
    db.commit()
    print("✅ All incidents processed")


def attempt_approval(db: Session, questionnaire: Questionnaire):
    """Attempt to approve questionnaire"""
    print_section("✅ STEP 6: Approval Workflow")
    
    # Check for unresolved incidents
    open_incidents = db.query(QuestionnaireIncident).filter(
        QuestionnaireIncident.questionnaire_id == questionnaire.id,
        QuestionnaireIncident.status == IncidentStatus.OPEN
    ).count()
    
    if open_incidents > 0:
        print(f"❌ Cannot approve: {open_incidents} incident(s) still open")
        print(f"   All critical incidents must be resolved or overridden before approval")
        return False
    
    print("✅ All incidents resolved")
    print("✅ Quality review passed")
    print("✅ Approving questionnaire...")
    
    questionnaire.status = QuestionnaireStatus.APPROVED
    questionnaire.reviewed_at = datetime.now()
    questionnaire.approved_at = datetime.now()
    db.commit()
    
    print(f"\n🎉 Questionnaire #{questionnaire.id} APPROVED!")
    print(f"   - Approved at: {questionnaire.approved_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   - This would now trigger Blue Line update in production")
    
    return True


def generate_summary(db: Session, material: Material):
    """Generate final summary"""
    print_section("📊 COMPLETE WORKFLOW SUMMARY")
    
    questionnaires = db.query(Questionnaire).filter(
        Questionnaire.material_id == material.id
    ).order_by(Questionnaire.version).all()
    
    print(f"Material: {material.reference_code} - {material.name}")
    print(f"Supplier: {material.supplier} ({material.supplier_code})")
    print(f"\nQuestionnaire History:")
    
    for q in questionnaires:
        print(f"\n  v{q.version} - {q.questionnaire_type.value}")
        print(f"  Status: {q.status.value}")
        print(f"  AI Risk Score: {q.ai_risk_score}/100" if q.ai_risk_score else "  No AI analysis")
        print(f"  Recommendation: {q.ai_recommendation}" if q.ai_recommendation else "")
        
        validations = db.query(QuestionnaireValidation).filter(
            QuestionnaireValidation.questionnaire_id == q.id
        ).count()
        
        incidents = db.query(QuestionnaireIncident).filter(
            QuestionnaireIncident.questionnaire_id == q.id
        ).count()
        
        if validations > 0:
            print(f"  Validations: {validations}")
        if incidents > 0:
            print(f"  Incidents: {incidents}")
    
    print("\n" + "="*80)
    print("  🎯 END-TO-END DEMO COMPLETE")
    print("="*80)
    print("\nWhat happened:")
    print("  1. ✅ Material with Blue Line established")
    print("  2. ✅ Initial questionnaire (v1) approved 6 months ago")
    print("  3. ⚠️  New rehomologation (v2) submitted with deviations")
    print("  4. 🤖 AI automatically validated and detected issues")
    print("  5. 🔴 Critical incidents auto-created for major deviations")
    print("  6. 🔧 Incidents resolved (override + escalation)")
    print("  7. ✅ Questionnaire approved after incident resolution")
    print("  8. 🔄 Blue Line would be updated with new values (in production)")
    
    print("\n📱 View in UI:")
    print(f"  • Questionnaires list: http://localhost:5173/questionnaires")
    print(f"  • V1 Details: http://localhost:5173/questionnaires/{questionnaires[0].id}")
    print(f"  • V2 Details: http://localhost:5173/questionnaires/{questionnaires[1].id}")
    print(f"  • Material: http://localhost:5173/materials/{material.id}")
    print()


async def main():
    """Main demo execution"""
    print("\n" + "🚀" * 40)
    print("  AUTOMATED QUESTIONNAIRE SYSTEM - END-TO-END DEMO")
    print("  AI-Powered Quality Control & Homologation Workflow")
    print("🚀" * 40)
    
    db = SessionLocal()
    try:
        # Clear previous data
        clear_demo_data(db)
        
        # Step 1: Setup
        material, blue_line = create_initial_scenario(db)
        
        # Step 2: Initial questionnaire (approved in the past)
        q1 = create_initial_questionnaire(db, material)
        
        # Step 3: New rehomologation with problems
        q2 = create_rehomologation_with_deviations(db, material, q1)
        
        # Step 4: Submit and validate with AI
        await submit_and_validate(db, q2)
        
        # Step 5: Resolve incidents
        demonstrate_incident_resolution(db, q2)
        
        # Step 6: Approve
        attempt_approval(db, q2)
        
        # Summary
        generate_summary(db, material)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

