from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import shutil
import tempfile
import json

from app.core.database import get_db
from app.core.config import settings
from app.models.questionnaire import Questionnaire, QuestionnaireStatus
from app.models.questionnaire_validation import QuestionnaireValidation
from app.models.questionnaire_incident import QuestionnaireIncident, IncidentStatus
from app.models.material import Material
from app.parsers.questionnaire_json_parser import QuestionnaireJSONParser
from app.schemas.questionnaire import (
    QuestionnaireCreate,
    QuestionnaireUpdate,
    QuestionnaireResponse,
    QuestionnaireValidationResponse,
    QuestionnaireIncidentResponse,
    QuestionnaireIncidentCreate,
    QuestionnaireIncidentUpdate,
    AIAnalysisResponse,
    QuestionnaireSubmitRequest,
    IncidentEscalateRequest,
    IncidentOverrideRequest,
    IncidentResolveRequest,
)
from app.services.questionnaire_validation_service import QuestionnaireValidationService
from app.services.questionnaire_ai_service import QuestionnaireAIService

router = APIRouter(prefix="/questionnaires", tags=["questionnaires"])


# ===== Questionnaire CRUD =====

@router.post("", response_model=QuestionnaireResponse, status_code=status.HTTP_201_CREATED)
def create_questionnaire(
    questionnaire: QuestionnaireCreate,
    db: Session = Depends(get_db)
):
    """Create a new questionnaire"""
    # Check if this is a rehomologation - find previous version
    if questionnaire.questionnaire_type.value == "REHOMOLOGATION":
        previous = db.query(Questionnaire).filter(
            Questionnaire.material_id == questionnaire.material_id,
            Questionnaire.supplier_code == questionnaire.supplier_code,
            Questionnaire.status == QuestionnaireStatus.APPROVED
        ).order_by(Questionnaire.version.desc()).first()
        
        if previous:
            questionnaire.previous_version_id = previous.id
            questionnaire.version = previous.version + 1
    
    db_questionnaire = Questionnaire(**questionnaire.model_dump())
    db.add(db_questionnaire)
    db.commit()
    db.refresh(db_questionnaire)
    
    return db_questionnaire


@router.get("", response_model=List[QuestionnaireResponse])
def list_questionnaires(
    material_id: Optional[int] = None,
    supplier_code: Optional[str] = None,
    status_filter: Optional[QuestionnaireStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all questionnaires with optional filters"""
    query = db.query(Questionnaire)
    
    if material_id:
        query = query.filter(Questionnaire.material_id == material_id)
    
    if supplier_code:
        query = query.filter(Questionnaire.supplier_code == supplier_code)
    
    if status_filter:
        query = query.filter(Questionnaire.status == status_filter)
    
    questionnaires = query.order_by(Questionnaire.created_at.desc()).offset(skip).limit(limit).all()
    
    return questionnaires


@router.get("/{questionnaire_id}", response_model=QuestionnaireResponse)
def get_questionnaire(questionnaire_id: int, db: Session = Depends(get_db)):
    """Get a specific questionnaire"""
    questionnaire = db.query(Questionnaire).filter(
        Questionnaire.id == questionnaire_id
    ).first()
    
    if not questionnaire:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Questionnaire {questionnaire_id} not found"
        )
    
    return questionnaire


@router.put("/{questionnaire_id}", response_model=QuestionnaireResponse)
def update_questionnaire(
    questionnaire_id: int,
    questionnaire_update: QuestionnaireUpdate,
    db: Session = Depends(get_db)
):
    """Update a questionnaire (only allowed if status is DRAFT)"""
    questionnaire = db.query(Questionnaire).filter(
        Questionnaire.id == questionnaire_id
    ).first()
    
    if not questionnaire:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Questionnaire {questionnaire_id} not found"
        )
    
    if questionnaire.status != QuestionnaireStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only update questionnaires in DRAFT status"
        )
    
    update_data = questionnaire_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(questionnaire, key, value)
    
    questionnaire.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(questionnaire)
    
    return questionnaire


@router.delete("/{questionnaire_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_questionnaire(questionnaire_id: int, db: Session = Depends(get_db)):
    """Delete a questionnaire (only allowed if status is DRAFT)"""
    questionnaire = db.query(Questionnaire).filter(
        Questionnaire.id == questionnaire_id
    ).first()
    
    if not questionnaire:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Questionnaire {questionnaire_id} not found"
        )
    
    if questionnaire.status != QuestionnaireStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only delete questionnaires in DRAFT status"
        )
    
    db.delete(questionnaire)
    db.commit()


# ===== Questionnaire Import =====

@router.post("/import/json", response_model=QuestionnaireResponse, status_code=status.HTTP_201_CREATED)
async def import_questionnaire_from_json(
    file: UploadFile = File(...),
    material_id: Optional[int] = Form(None),
    material_code: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Import a questionnaire from JSON file (Lluch format).
    
    The JSON file should follow the Lluch format:
    {
      "requestId": 2027,
      "data": [
        {
          "fieldCode": "q3t1s2f15",
          "fieldName": "Supplier Name",
          "fieldType": "inputText",
          "value": "..."
        },
        ...
      ]
    }
    
    Material can be specified by:
    - material_id: Direct material ID
    - material_code: Material reference code (will be extracted from JSON if not provided)
    """
    # Validate file type
    if not file.filename.endswith('.json') and not file.filename.endswith('.txt'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JSON files (.json or .txt) are supported"
        )
    
    # Save file temporarily
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"questionnaire_{timestamp}_{file.filename}"
    file_path = upload_dir / filename
    
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Parse JSON
        parser = QuestionnaireJSONParser(str(file_path))
        parsed_data = parser.parse()
        
        # Extract metadata
        metadata = parsed_data.get("metadata", {})
        responses = parsed_data.get("responses", {})
        
        # Determine material
        material = None
        if material_id:
            material = db.query(Material).filter(Material.id == material_id).first()
            if not material:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Material with ID {material_id} not found"
                )
        elif material_code:
            material = db.query(Material).filter(Material.reference_code == material_code).first()
            if not material:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Material with code '{material_code}' not found"
                )
        else:
            # Try to extract from JSON metadata
            product_code = metadata.get("product_code", "")
            product_name = metadata.get("product_name", "")
            
            # Try product_code first
            if product_code and product_code.startswith("[") and "]" in product_code:
                material_code_from_json = product_code.split("]")[0].replace("[", "")
                material = db.query(Material).filter(
                    Material.reference_code == material_code_from_json
                ).first()
            
            # If not found, try product_name (format: [BASIL0003] H.E. BASILIC INDES)
            if not material and product_name and product_name.startswith("[") and "]" in product_name:
                material_code_from_json = product_name.split("]")[0].replace("[", "")
                material = db.query(Material).filter(
                    Material.reference_code == material_code_from_json
                ).first()
        
        if not material:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Material not found. Please provide material_id or material_code, "
                       "or ensure the JSON contains a product code in format [MATERIAL_CODE]."
            )
        
        # Extract supplier code
        supplier_code = metadata.get("supplier_name", "SUPPLIER-UNKNOWN")
        if len(supplier_code) > 100:
            supplier_code = supplier_code[:100]
        
        # Determine questionnaire type and version
        from app.models.questionnaire import QuestionnaireType
        questionnaire_type = QuestionnaireType.INITIAL_HOMOLOGATION
        existing_count = db.query(Questionnaire).filter(
            Questionnaire.material_id == material.id,
            Questionnaire.supplier_code == supplier_code
        ).count()
        
        version = existing_count + 1
        previous_version_id = None
        
        if version > 1:
            questionnaire_type = QuestionnaireType.REHOMOLOGATION
            previous = db.query(Questionnaire).filter(
                Questionnaire.material_id == material.id,
                Questionnaire.supplier_code == supplier_code
            ).order_by(Questionnaire.version.desc()).first()
            
            if previous:
                previous_version_id = previous.id
        
        # Get default template if available
        from app.models.questionnaire_template import QuestionnaireTemplate, TemplateType
        default_template = db.query(QuestionnaireTemplate).filter(
            QuestionnaireTemplate.is_default == True,
            QuestionnaireTemplate.template_type == TemplateType.INITIAL_HOMOLOGATION
        ).first()
        
        # Create questionnaire
        questionnaire = Questionnaire(
            material_id=material.id,
            supplier_code=supplier_code,
            questionnaire_type=questionnaire_type,
            version=version,
            previous_version_id=previous_version_id,
            template_id=default_template.id if default_template else None,
            responses={
                **responses,
                "_metadata": metadata,
                "_request_id": parsed_data.get("request_id"),
                "_imported_from": filename
            },
            status=QuestionnaireStatus.DRAFT
        )
        
        db.add(questionnaire)
        db.commit()
        db.refresh(questionnaire)
        
        return questionnaire
        
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON format: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error importing questionnaire: {str(e)}"
        )


# ===== Questionnaire Actions =====

@router.post("/{questionnaire_id}/submit", response_model=QuestionnaireResponse)
async def submit_questionnaire(
    questionnaire_id: int,
    submit_request: QuestionnaireSubmitRequest,
    db: Session = Depends(get_db)
):
    """Submit questionnaire for review - triggers validation and AI analysis"""
    questionnaire = db.query(Questionnaire).filter(
        Questionnaire.id == questionnaire_id
    ).first()
    
    if not questionnaire:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Questionnaire {questionnaire_id} not found"
        )
    
    if questionnaire.status != QuestionnaireStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only submit questionnaires in DRAFT status"
        )
    
    # Update status
    questionnaire.status = QuestionnaireStatus.SUBMITTED
    questionnaire.submitted_at = datetime.utcnow()
    db.commit()
    
    # Run validation
    validation_service = QuestionnaireValidationService(db)
    validation_service.validate_questionnaire(questionnaire_id)
    
    # Run AI analysis
    ai_service = QuestionnaireAIService(db)
    ai_analysis = await ai_service.analyze_risk_profile(questionnaire_id)
    
    # Update questionnaire with AI results
    questionnaire.ai_risk_score = ai_analysis["risk_score"]
    questionnaire.ai_summary = ai_analysis["summary"]
    questionnaire.ai_recommendation = ai_analysis["recommendation"]
    questionnaire.status = QuestionnaireStatus.IN_REVIEW
    db.commit()
    db.refresh(questionnaire)
    
    return questionnaire


@router.post("/{questionnaire_id}/approve", response_model=QuestionnaireResponse)
def approve_questionnaire(
    questionnaire_id: int,
    db: Session = Depends(get_db)
):
    """Approve questionnaire - updates Blue Line if applicable"""
    questionnaire = db.query(Questionnaire).filter(
        Questionnaire.id == questionnaire_id
    ).first()
    
    if not questionnaire:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Questionnaire {questionnaire_id} not found"
        )
    
    if questionnaire.status != QuestionnaireStatus.IN_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only approve questionnaires in IN_REVIEW status"
        )
    
    # Check for unresolved critical incidents
    unresolved_incidents = db.query(QuestionnaireIncident).filter(
        QuestionnaireIncident.questionnaire_id == questionnaire_id,
        QuestionnaireIncident.status == IncidentStatus.OPEN
    ).count()
    
    if unresolved_incidents > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve: {unresolved_incidents} unresolved incident(s) remaining"
        )
    
    questionnaire.status = QuestionnaireStatus.APPROVED
    questionnaire.approved_at = datetime.utcnow()
    questionnaire.reviewed_at = datetime.utcnow()
    db.commit()
    db.refresh(questionnaire)
    
    # TODO: Trigger Blue Line update
    
    return questionnaire


@router.post("/{questionnaire_id}/reject", response_model=QuestionnaireResponse)
def reject_questionnaire(
    questionnaire_id: int,
    db: Session = Depends(get_db)
):
    """Reject questionnaire"""
    questionnaire = db.query(Questionnaire).filter(
        Questionnaire.id == questionnaire_id
    ).first()
    
    if not questionnaire:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Questionnaire {questionnaire_id} not found"
        )
    
    questionnaire.status = QuestionnaireStatus.REJECTED
    questionnaire.reviewed_at = datetime.utcnow()
    db.commit()
    db.refresh(questionnaire)
    
    return questionnaire


# ===== Validations =====

@router.get("/{questionnaire_id}/validations", response_model=List[QuestionnaireValidationResponse])
def get_questionnaire_validations(
    questionnaire_id: int,
    db: Session = Depends(get_db)
):
    """Get all validations for a questionnaire"""
    validations = db.query(QuestionnaireValidation).filter(
        QuestionnaireValidation.questionnaire_id == questionnaire_id
    ).all()
    
    return validations


@router.post("/{questionnaire_id}/validate", response_model=List[QuestionnaireValidationResponse])
def validate_questionnaire(
    questionnaire_id: int,
    db: Session = Depends(get_db)
):
    """Manually trigger validation"""
    validation_service = QuestionnaireValidationService(db)
    validations = validation_service.validate_questionnaire(questionnaire_id)
    
    return validations


# ===== AI Analysis =====

@router.post("/{questionnaire_id}/ai-analysis", response_model=AIAnalysisResponse)
async def get_ai_analysis(
    questionnaire_id: int,
    db: Session = Depends(get_db)
):
    """Get AI analysis for questionnaire"""
    ai_service = QuestionnaireAIService(db)
    analysis = await ai_service.analyze_risk_profile(questionnaire_id)
    
    return analysis


# ===== Incidents =====

@router.get("/{questionnaire_id}/incidents", response_model=List[QuestionnaireIncidentResponse])
def get_questionnaire_incidents(
    questionnaire_id: int,
    db: Session = Depends(get_db)
):
    """Get all incidents for a questionnaire"""
    incidents = db.query(QuestionnaireIncident).filter(
        QuestionnaireIncident.questionnaire_id == questionnaire_id
    ).all()
    
    return incidents


@router.post("/incidents", response_model=QuestionnaireIncidentResponse, status_code=status.HTTP_201_CREATED)
def create_incident(
    incident: QuestionnaireIncidentCreate,
    db: Session = Depends(get_db)
):
    """Create a new incident manually"""
    db_incident = QuestionnaireIncident(**incident.model_dump())
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    
    return db_incident


@router.put("/incidents/{incident_id}", response_model=QuestionnaireIncidentResponse)
def update_incident(
    incident_id: int,
    incident_update: QuestionnaireIncidentUpdate,
    db: Session = Depends(get_db)
):
    """Update an incident"""
    incident = db.query(QuestionnaireIncident).filter(
        QuestionnaireIncident.id == incident_id
    ).first()
    
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found"
        )
    
    update_data = incident_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(incident, key, value)
    
    incident.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(incident)
    
    return incident


@router.post("/incidents/{incident_id}/escalate", response_model=QuestionnaireIncidentResponse)
def escalate_incident(
    incident_id: int,
    escalate_request: IncidentEscalateRequest,
    db: Session = Depends(get_db)
):
    """Escalate incident to supplier"""
    incident = db.query(QuestionnaireIncident).filter(
        QuestionnaireIncident.id == incident_id
    ).first()
    
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found"
        )
    
    from app.models.questionnaire_incident import IncidentStatus, ResolutionAction
    
    incident.status = IncidentStatus.ESCALATED_TO_SUPPLIER
    incident.resolution_action = ResolutionAction.ESCALATED
    incident.supplier_notified_at = datetime.utcnow()
    
    if escalate_request.notes:
        incident.resolution_notes = escalate_request.notes
    
    incident.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(incident)
    
    return incident


@router.post("/incidents/{incident_id}/override", response_model=QuestionnaireIncidentResponse)
def override_incident(
    incident_id: int,
    override_request: IncidentOverrideRequest,
    db: Session = Depends(get_db)
):
    """Override incident with justification"""
    incident = db.query(QuestionnaireIncident).filter(
        QuestionnaireIncident.id == incident_id
    ).first()
    
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found"
        )
    
    from app.models.questionnaire_incident import IncidentStatus, ResolutionAction
    
    incident.status = IncidentStatus.OVERRIDDEN
    incident.resolution_action = ResolutionAction.USER_OVERRIDE
    incident.override_justification = override_request.justification
    incident.resolved_at = datetime.utcnow()
    incident.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(incident)
    
    return incident


@router.post("/incidents/{incident_id}/resolve", response_model=QuestionnaireIncidentResponse)
def resolve_incident(
    incident_id: int,
    resolve_request: IncidentResolveRequest,
    db: Session = Depends(get_db)
):
    """Mark incident as resolved"""
    incident = db.query(QuestionnaireIncident).filter(
        QuestionnaireIncident.id == incident_id
    ).first()
    
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found"
        )
    
    from app.models.questionnaire_incident import IncidentStatus, ResolutionAction
    
    incident.status = IncidentStatus.RESOLVED
    incident.resolution_action = ResolutionAction.SUPPLIER_CORRECTION
    incident.resolution_notes = resolve_request.resolution_notes
    incident.resolved_at = datetime.utcnow()
    incident.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(incident)
    
    return incident

