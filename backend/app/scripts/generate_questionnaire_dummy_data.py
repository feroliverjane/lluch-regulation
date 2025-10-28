"""
Script to generate dummy questionnaire data for demo purposes.

This script creates:
- Questionnaires with various statuses
- Validations for each questionnaire
- Incidents for critical validations
- AI analysis results
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.material import Material
from app.models.blue_line import BlueLine
from app.models.questionnaire import Questionnaire, QuestionnaireType, QuestionnaireStatus
from app.models.questionnaire_validation import QuestionnaireValidation, ValidationType, ValidationSeverity
from app.models.questionnaire_incident import QuestionnaireIncident, IncidentStatus, ResolutionAction
from app.models.user import User


def generate_sample_responses(material_type: str, has_deviations: bool = False) -> dict:
    """Generate sample questionnaire responses"""
    base_responses = {
        # Basic Information
        "company_name": "Global Ingredients Ltd.",
        "contact_person": "John Smith",
        "contact_email": "john.smith@globalingredients.com",
        "contact_phone": "+44 20 1234 5678",
        
        # Certifications
        "quality_certificate": "ISO 9001:2015",
        "organic_certified": "Yes" if random.choice([True, False]) else "No",
        "kosher_certified": "Yes" if random.choice([True, False]) else "No",
        "halal_certified": "No",
        "fair_trade_certified": "No",
        
        # Sustainability
        "sustainable_sourcing": "Yes",
        "carbon_neutral": "No",
        "endangered_species_used": "No",
        "sustainability_score": 75,
        
        # Allergens
        "allergen_declaration": "None",
        "gluten_free": "Yes",
        "lactose_free": "Yes",
        
        # Quality Parameters
        "purity_percentage": "99.5",
        "moisture_content": "0.2",
        "ash_content": "0.1",
        "heavy_metals_compliant": "Yes",
        "microbiological_compliant": "Yes",
        
        # Supply Chain
        "country_of_origin": "Spain",
        "manufacturing_site": "Barcelona Production Facility",
        "batch_tracking_available": "Yes",
        "shelf_life_months": "24",
        
        # Documentation
        "technical_data_sheet_available": "Yes",
        "safety_data_sheet_available": "Yes",
        "coa_provided": "Yes",
        
        # Additional
        "gmo_free": "Yes",
        "irradiation_used": "No",
        "additional_comments": "Complies with all EU regulations. Premium grade material."
    }
    
    # Introduce deviations for testing
    if has_deviations:
        base_responses["purity_percentage"] = "95.2"  # Lower purity
        base_responses["moisture_content"] = "2.1"  # Higher moisture
        base_responses["sustainability_score"] = 45  # Lower score
        base_responses["allergen_declaration"] = "May contain traces of nuts"  # Changed
    
    return base_responses


def clear_existing_data(db: Session):
    """Clear existing questionnaire data"""
    print("🗑️  Clearing existing questionnaire data...")
    db.query(QuestionnaireIncident).delete()
    db.query(QuestionnaireValidation).delete()
    db.query(Questionnaire).delete()
    db.commit()
    print("✅ Cleared")


def create_questionnaires(db: Session):
    """Create sample questionnaires"""
    print("\n📋 Creating questionnaires...")
    
    # Get some materials with Blue Lines
    materials_with_bl = db.query(Material).join(BlueLine).limit(3).all()
    
    if not materials_with_bl:
        print("⚠️  No materials with Blue Lines found. Run generate_blue_line_dummy_data.py first")
        return []
    
    questionnaires = []
    
    # Scenario 1: Approved questionnaire (old version)
    material1 = materials_with_bl[0]
    q1 = Questionnaire(
        material_id=material1.id,
        supplier_code=material1.supplier_code or "LLUCH-GLOBAL-001",
        questionnaire_type=QuestionnaireType.INITIAL_HOMOLOGATION,
        version=1,
        responses=generate_sample_responses(material1.material_type, has_deviations=False),
        status=QuestionnaireStatus.APPROVED,
        ai_risk_score=15,
        ai_summary="✅ Excellent submission. All parameters within expected ranges. No significant concerns identified.",
        ai_recommendation="APPROVE",
        created_at=datetime.now() - timedelta(days=180),
        submitted_at=datetime.now() - timedelta(days=179),
        reviewed_at=datetime.now() - timedelta(days=178),
        approved_at=datetime.now() - timedelta(days=178)
    )
    db.add(q1)
    db.commit()
    db.refresh(q1)
    questionnaires.append(q1)
    print(f"✅ Created approved questionnaire #{q1.id} for {material1.reference_code}")
    
    # Scenario 2: Rehomologation with deviations (IN_REVIEW with incidents)
    q2 = Questionnaire(
        material_id=material1.id,
        supplier_code=material1.supplier_code or "LLUCH-GLOBAL-001",
        questionnaire_type=QuestionnaireType.REHOMOLOGATION,
        version=2,
        previous_version_id=q1.id,
        responses=generate_sample_responses(material1.material_type, has_deviations=True),
        status=QuestionnaireStatus.IN_REVIEW,
        ai_risk_score=65,
        ai_summary="⚠️ Significant deviations detected from previous version and Blue Line values. Purity has decreased by 4.3%, moisture content has increased significantly. Sustainability score has dropped 30 points. Manual review recommended before approval.",
        ai_recommendation="REVIEW",
        created_at=datetime.now() - timedelta(days=7),
        submitted_at=datetime.now() - timedelta(days=6),
        reviewed_at=None
    )
    db.add(q2)
    db.commit()
    db.refresh(q2)
    questionnaires.append(q2)
    print(f"✅ Created rehomologation questionnaire #{q2.id} with deviations")
    
    # Create validations for q2
    validations = [
        QuestionnaireValidation(
            questionnaire_id=q2.id,
            validation_type=ValidationType.BLUE_LINE_COMPARISON,
            field_name="purity_percentage",
            expected_value="99.5",
            actual_value="95.2",
            deviation_percentage=4.32,
            severity=ValidationSeverity.WARNING,
            requires_action=True,
            message="Purity has decreased from 99.5% to 95.2% (-4.3%). This is below the warning threshold."
        ),
        QuestionnaireValidation(
            questionnaire_id=q2.id,
            validation_type=ValidationType.VERSION_COMPARISON,
            field_name="moisture_content",
            expected_value="0.2",
            actual_value="2.1",
            deviation_percentage=950.0,
            severity=ValidationSeverity.CRITICAL,
            requires_action=True,
            message="Moisture content has increased dramatically from 0.2% to 2.1% (+950%). This requires immediate attention."
        ),
        QuestionnaireValidation(
            questionnaire_id=q2.id,
            validation_type=ValidationType.BLUE_LINE_COMPARISON,
            field_name="sustainability_score",
            expected_value="75",
            actual_value="45",
            deviation_percentage=40.0,
            severity=ValidationSeverity.CRITICAL,
            requires_action=True,
            message="Sustainability score has dropped from 75 to 45 (-40%). This exceeds the critical threshold."
        )
    ]
    
    for v in validations:
        db.add(v)
    db.commit()
    print(f"✅ Created {len(validations)} validations for questionnaire #{q2.id}")
    
    # Create incidents for critical validations
    critical_validations = [v for v in validations if v.severity == ValidationSeverity.CRITICAL]
    incidents = []
    for v in critical_validations:
        incident = QuestionnaireIncident(
            questionnaire_id=q2.id,
            validation_id=v.id,
            field_name=v.field_name,
            issue_description=f"Critical deviation detected: {v.message}",
            status=IncidentStatus.OPEN,
            resolution_action=ResolutionAction.PENDING
        )
        db.add(incident)
        incidents.append(incident)
    db.commit()
    print(f"✅ Created {len(incidents)} critical incidents for questionnaire #{q2.id}")
    
    # Scenario 3: Draft questionnaire (no validation yet)
    if len(materials_with_bl) > 1:
        material2 = materials_with_bl[1]
        q3 = Questionnaire(
            material_id=material2.id,
            supplier_code=material2.supplier_code or "LLUCH-EURO-002",
            questionnaire_type=QuestionnaireType.INITIAL_HOMOLOGATION,
            version=1,
            responses=generate_sample_responses(material2.material_type, has_deviations=False),
            status=QuestionnaireStatus.DRAFT,
            created_at=datetime.now() - timedelta(days=2)
        )
        db.add(q3)
        db.commit()
        db.refresh(q3)
        questionnaires.append(q3)
        print(f"✅ Created draft questionnaire #{q3.id} for {material2.reference_code}")
    
    # Scenario 4: Another approved questionnaire with good scores
    if len(materials_with_bl) > 2:
        material3 = materials_with_bl[2]
        q4 = Questionnaire(
            material_id=material3.id,
            supplier_code=material3.supplier_code or "LLUCH-ASIA-003",
            questionnaire_type=QuestionnaireType.INITIAL_HOMOLOGATION,
            version=1,
            responses=generate_sample_responses(material3.material_type, has_deviations=False),
            status=QuestionnaireStatus.APPROVED,
            ai_risk_score=8,
            ai_summary="✅ Outstanding submission. All parameters exceed expectations. Strong sustainability credentials. Highly recommended for approval.",
            ai_recommendation="APPROVE",
            created_at=datetime.now() - timedelta(days=90),
            submitted_at=datetime.now() - timedelta(days=89),
            reviewed_at=datetime.now() - timedelta(days=88),
            approved_at=datetime.now() - timedelta(days=88)
        )
        db.add(q4)
        db.commit()
        db.refresh(q4)
        questionnaires.append(q4)
        print(f"✅ Created approved questionnaire #{q4.id} for {material3.reference_code}")
    
    return questionnaires


def print_summary(db: Session):
    """Print a summary of generated data"""
    print("\n" + "="*60)
    print("📊 QUESTIONNAIRE DATA GENERATION SUMMARY")
    print("="*60)
    
    total_questionnaires = db.query(Questionnaire).count()
    total_validations = db.query(QuestionnaireValidation).count()
    total_incidents = db.query(QuestionnaireIncident).count()
    
    print(f"\n✅ Total Questionnaires: {total_questionnaires}")
    print(f"   - Draft: {db.query(Questionnaire).filter(Questionnaire.status == QuestionnaireStatus.DRAFT).count()}")
    print(f"   - Submitted: {db.query(Questionnaire).filter(Questionnaire.status == QuestionnaireStatus.SUBMITTED).count()}")
    print(f"   - In Review: {db.query(Questionnaire).filter(Questionnaire.status == QuestionnaireStatus.IN_REVIEW).count()}")
    print(f"   - Approved: {db.query(Questionnaire).filter(Questionnaire.status == QuestionnaireStatus.APPROVED).count()}")
    print(f"   - Rejected: {db.query(Questionnaire).filter(Questionnaire.status == QuestionnaireStatus.REJECTED).count()}")
    
    print(f"\n✅ Total Validations: {total_validations}")
    print(f"   - Critical: {db.query(QuestionnaireValidation).filter(QuestionnaireValidation.severity == ValidationSeverity.CRITICAL).count()}")
    print(f"   - Warning: {db.query(QuestionnaireValidation).filter(QuestionnaireValidation.severity == ValidationSeverity.WARNING).count()}")
    print(f"   - Info: {db.query(QuestionnaireValidation).filter(QuestionnaireValidation.severity == ValidationSeverity.INFO).count()}")
    
    print(f"\n✅ Total Incidents: {total_incidents}")
    print(f"   - Open: {db.query(QuestionnaireIncident).filter(QuestionnaireIncident.status == IncidentStatus.OPEN).count()}")
    print(f"   - Escalated: {db.query(QuestionnaireIncident).filter(QuestionnaireIncident.status == IncidentStatus.ESCALATED_TO_SUPPLIER).count()}")
    print(f"   - Resolved: {db.query(QuestionnaireIncident).filter(QuestionnaireIncident.status == IncidentStatus.RESOLVED).count()}")
    print(f"   - Overridden: {db.query(QuestionnaireIncident).filter(QuestionnaireIncident.status == IncidentStatus.OVERRIDDEN).count()}")
    
    print("\n" + "="*60)
    print("✅ Dummy data generation complete!")
    print("="*60)
    print("\nYou can now:")
    print("  1. View questionnaires at http://localhost:5173/questionnaires")
    print("  2. API endpoint: http://localhost:8000/api/questionnaires")
    print("  3. Check the one IN_REVIEW to see validations and incidents")
    print("\n")


def main():
    """Main function"""
    print("\n🚀 Starting Questionnaire Dummy Data Generation\n")
    
    db = SessionLocal()
    try:
        # Clear existing data
        clear_existing_data(db)
        
        # Create questionnaires with validations and incidents
        questionnaires = create_questionnaires(db)
        
        if questionnaires:
            # Print summary
            print_summary(db)
        else:
            print("\n⚠️  No data created. Ensure materials and Blue Lines exist first.")
            print("   Run: python app/scripts/generate_blue_line_dummy_data.py")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

