from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import shutil
import tempfile
import json
import logging
import re

from app.core.database import get_db
from app.core.config import settings
from app.models.questionnaire import Questionnaire, QuestionnaireStatus
from app.models.questionnaire_validation import QuestionnaireValidation
from app.models.questionnaire_incident import QuestionnaireIncident, IncidentStatus
from app.models.material import Material
from app.parsers.questionnaire_json_parser import QuestionnaireJSONParser
from sqlalchemy import or_, func
from app.schemas.questionnaire import (
    QuestionnaireCreate,
    QuestionnaireUpdate,
    QuestionnaireResponse,
    QuestionnaireImportResponse,
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
from app.services.material_supplier_comparison import MaterialSupplierComparisonService
from app.schemas.material_supplier import ComparisonResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/questionnaires", tags=["questionnaires"])


# ===== Questionnaire CRUD =====

@router.post("", response_model=QuestionnaireResponse, status_code=status.HTTP_201_CREATED)
async def create_questionnaire(
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
    
    # Automatically validate against Blue Line
    try:
        validation_service = QuestionnaireValidationService(db)
        validation_service.validate_questionnaire(db_questionnaire.id)
    except Exception as e:
        # Log error but don't fail questionnaire creation
        logger.warning(f"Validation failed for questionnaire {db_questionnaire.id}: {e}")
    
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

def find_similar_materials(
    db: Session,
    product_name: str = None,
    product_code: str = None,
    cas_number: str = None,
    einecs_number: str = None,
    botanical_name: str = None,
    country_origin: str = None,
    limit: int = 5
) -> List[Material]:
    """
    Find materials similar to the given product information.
    Priority order:
    1. EINECS number (if available - most reliable for EU materials, exact match)
    2. CAS number (exact match - most reliable)
    3. Botanical name + Country origin (if both match, very likely same material)
    4. Name keywords (less specific but useful)
    5. Botanical name only (if available)
    
    Returns materials ordered by match quality (EINECS matches first, then CAS, then botanical matches).
    """
    from app.models.blue_line import BlueLine
    
    query = db.query(Material).filter(Material.is_active == True)
    einecs_matches = []
    cas_matches = []
    botanical_matches = []
    keyword_matches = []
    
    # PRIORITY 1: Search by EINECS number first (if available - most reliable for EU materials)
    if einecs_number and einecs_number.strip():
        einecs_clean = einecs_number.strip()
        
        # Search EINECS in BlueLine.responses (fieldCode q3t1s2f24)
        # Get all active materials and check their blue lines
        all_materials = query.all()
        
        for mat in all_materials:
            # Check if material has blue lines
            if mat.blue_lines:
                blue_line = mat.blue_lines[0]
                if blue_line and blue_line.responses:
                    # Check if EINECS field exists in BlueLine responses
                    einecs_field = blue_line.responses.get("q3t1s2f24")
                    if einecs_field:
                        # Extract value (could be dict with "value" key or direct string)
                        einecs_value = einecs_field.get("value") if isinstance(einecs_field, dict) else einecs_field
                        if einecs_value and str(einecs_value).strip() == einecs_clean:
                            einecs_matches.append(mat)
                            if len(einecs_matches) >= limit:
                                break
        
        # If we found exact EINECS matches, return them immediately (highest priority)
        if einecs_matches:
            return einecs_matches[:limit]
    
    # PRIORITY 2: Search by CAS number (exact match - most reliable)
    if cas_number and cas_number.strip():
        cas_clean = cas_number.strip()
        cas_matches = query.filter(Material.cas_number == cas_clean).limit(limit).all()
        # If we found exact CAS matches, return them immediately
        if cas_matches:
            return cas_matches[:limit]
    
    # PRIORITY 2: Search by botanical name (in description field)
    # Botanical name is often stored in description like "Basil essential oil - Ocimum basilicum L."
    if botanical_name and botanical_name.strip():
        botanical_clean = botanical_name.strip().upper()
        # Extract genus and species (e.g., "Ocimum basilicum" from "Ocimum basilicum L.")
        botanical_parts = botanical_clean.split()
        if len(botanical_parts) >= 2:
            genus_species = f"{botanical_parts[0]} {botanical_parts[1]}"
            # Search in description field (where botanical name is often stored)
            botanical_conditions = [
                func.upper(Material.description).contains(botanical_clean),
                func.upper(Material.description).contains(genus_species)
            ]
            # Also search in name field (sometimes botanical name is in the name)
            botanical_conditions.append(
                func.upper(Material.name).contains(genus_species)
            )
            
            botanical_query = query.filter(or_(*botanical_conditions))
            
            # If country_origin is also provided, prioritize matches that mention the country
            if country_origin:
                # Country codes are usually 2 letters (e.g., "IN" for India)
                country_upper = country_origin.strip().upper()
                if len(country_upper) == 2:
                    # Search for country in description or name
                    country_conditions = [
                        func.upper(Material.description).contains(country_upper),
                        func.upper(Material.name).contains(country_upper)
                    ]
                    botanical_query = botanical_query.filter(or_(*country_conditions))
            
            botanical_matches = botanical_query.limit(limit * 2).all()
    
    # PRIORITY 3: Search by name keywords (if no botanical match found or to supplement)
    keywords = []
    if product_name:
        # Remove brackets and codes, extract meaningful words
        clean_name = product_name.upper()
        # Remove patterns like [CODE]
        clean_name = re.sub(r'\[.*?\]', '', clean_name)
        # Extract words (3+ characters, excluding common words)
        words = [w for w in clean_name.split() if len(w) >= 3 and w not in ['THE', 'AND', 'OIL', 'ESSENTIAL', 'H.E.', 'E.', 'INDES', 'INDIA']]
        keywords.extend(words)
    
    # Also use product code as keyword if it contains letters
    if product_code:
        # Extract letters from code (e.g., "BASIL" from "BASIL0003")
        code_letters = ''.join([c for c in product_code.upper() if c.isalpha()])
        if len(code_letters) >= 3:
            keywords.append(code_letters)
    
    # Search by keywords in name and reference_code
    if keywords:
        keyword_conditions = []
        for keyword in keywords:
            keyword_upper = keyword.upper()
            keyword_conditions.append(
                func.upper(Material.name).contains(keyword_upper)
            )
            keyword_conditions.append(
                func.upper(Material.reference_code).contains(keyword_upper)
            )
        
        if keyword_conditions:
            keyword_matches = query.filter(or_(*keyword_conditions)).limit(limit * 2).all()
    
    # Combine results: botanical matches first (if found), then keyword matches
    # Remove duplicates while preserving order
    seen_ids = set()
    unique_materials = []
    
    # Add botanical matches first (higher priority)
    for mat in botanical_matches:
        if mat.id not in seen_ids:
            seen_ids.add(mat.id)
            unique_materials.append(mat)
    
    # Add keyword matches
    for mat in keyword_matches:
        if mat.id not in seen_ids:
            seen_ids.add(mat.id)
            unique_materials.append(mat)
    
    return unique_materials[:limit]


@router.post("/import/json", response_model=QuestionnaireImportResponse, status_code=status.HTTP_201_CREATED)
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
        
        # Get critical fields for better material detection
        critical_fields = parser.get_critical_fields()
        
        # Determine material
        material = None
        detected_material_code = None  # Track if we detected a code from JSON
        
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
            
            # Try product_code first (with or without brackets)
            if product_code:
                # Try with brackets format: [BASIL0003]
                if product_code.startswith("[") and "]" in product_code:
                    detected_material_code = product_code.split("]")[0].replace("[", "")
                    material = db.query(Material).filter(
                        Material.reference_code == detected_material_code
                    ).first()
                # Try without brackets: BASIL0003
                elif not material and product_code.strip():
                    detected_material_code = product_code.strip()
                    material = db.query(Material).filter(
                        Material.reference_code == detected_material_code
                    ).first()
            
            # If not found, try product_name (format: [BASIL0003] H.E. BASILIC INDES)
            if not material and product_name and product_name.startswith("[") and "]" in product_name:
                detected_material_code = product_name.split("]")[0].replace("[", "")
                material = db.query(Material).filter(
                    Material.reference_code == detected_material_code
                ).first()
        
        # If material not found but we detected a code from JSON, try to find similar materials
        if not material and detected_material_code:
            # Extract additional info for similarity search from critical fields
            cas_field = critical_fields.get("cas_number", {})
            einecs_field = critical_fields.get("einecs_number", {})
            botanical_field = critical_fields.get("botanical_name", {})
            country_field = critical_fields.get("country_origin", {})
            
            cas_number = cas_field.get("value", "") if cas_field else ""
            einecs_number = einecs_field.get("value", "") if einecs_field else ""
            botanical_name = botanical_field.get("value", "") if botanical_field else ""
            country_origin = country_field.get("value", "") if country_field else ""
            
            # Try to find similar materials
            similar_materials = find_similar_materials(
                db=db,
                product_name=product_name,
                product_code=detected_material_code,
                cas_number=cas_number,
                einecs_number=einecs_number,
                botanical_name=botanical_name,
                country_origin=country_origin
            )
            
            if similar_materials:
                # Found similar materials - return them as suggestions with CAS and EINECS info
                from app.models.blue_line import BlueLine
                similar_info = []
                for m in similar_materials:
                    # Get EINECS from BlueLine if available
                    einecs_value = None
                    if m.blue_lines:
                        blue_line = m.blue_lines[0]
                        if blue_line and blue_line.responses:
                            einecs_field = blue_line.responses.get("q3t1s2f24")
                            if einecs_field:
                                einecs_value = einecs_field.get("value") if isinstance(einecs_field, dict) else einecs_field
                    
                    # Build info string
                    info_parts = [f"{m.reference_code} ({m.name})"]
                    
                    # Add EINECS info
                    if einecs_value:
                        einecs_match = "✅" if einecs_number and str(einecs_value).strip() == einecs_number.strip() else ""
                        info_parts.append(f"EINECS: {einecs_value}{einecs_match}")
                    elif einecs_number:
                        info_parts.append("EINECS: N/A")
                    
                    # Add CAS info
                    cas_info = f"CAS: {m.cas_number}" if m.cas_number else "CAS: N/A"
                    cas_warning = ""
                    if cas_number and m.cas_number and cas_number.strip() != m.cas_number.strip():
                        cas_warning = " ⚠️ (CAS diferente)"
                    info_parts.append(f"{cas_info}{cas_warning}")
                    
                    similar_info.append(" - ".join(info_parts))
                
                warning_msg = ""
                if einecs_number:
                    warning_msg = "Si el EINECS coincide exactamente, es muy probable que sea el mismo material (incluso si el CAS es diferente). "
                warning_msg += "Si los CAS son diferentes, pueden ser materiales distintos aunque tengan nombres similares."
                
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"SIMILAR_MATERIALS_FOUND: El material '{detected_material_code}' no existe, pero se encontraron materiales similares: "
                           f"{' | '.join(similar_info)}. "
                           f"⚠️ {warning_msg} "
                           f"¿Deseas usar uno de estos materiales o crear uno nuevo?"
                )
            else:
                # No similar materials found - return new material error
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"NEW_MATERIAL_DETECTED: El material '{detected_material_code}' fue detectado del JSON pero no existe en el sistema. "
                           f"Por favor, crea primero el material '{detected_material_code}' antes de importar el cuestionario."
                )
        
        # If no material found and no code detected
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
        
        # Extract request_id from parsed data
        request_id = parsed_data.get("request_id")
        
        # Check if questionnaire with same request_id already exists
        # This prevents duplicate imports of the same questionnaire file
        existing_questionnaire = None
        if request_id:
            # Query all questionnaires for this material and check request_id in Python
            # This is more compatible with SQLite JSON handling
            all_questionnaires = db.query(Questionnaire).filter(
                Questionnaire.material_id == material.id
            ).all()
            
            for q in all_questionnaires:
                if q.responses and isinstance(q.responses, dict):
                    stored_request_id = q.responses.get("_request_id")
                    if stored_request_id == request_id:
                        existing_questionnaire = q
                        break
        
        if existing_questionnaire:
            # Questionnaire already imported - return existing one
            logger.info(
                f"Questionnaire with request_id {request_id} already exists (ID: {existing_questionnaire.id}). "
                f"Returning existing questionnaire instead of creating duplicate."
            )
            questionnaire = existing_questionnaire
            # Still need to perform comparison if Blue Line exists
            # (comparison will be done after this if block)
        else:
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
                    "_request_id": request_id,
                    "_imported_from": filename
                },
                status=QuestionnaireStatus.DRAFT
            )
            
            db.add(questionnaire)
            db.commit()
            db.refresh(questionnaire)
        
        # Automatically validate against Blue Line
        try:
            validation_service = QuestionnaireValidationService(db)
            validation_service.validate_questionnaire(questionnaire.id)
        except Exception as e:
            # Log error but don't fail questionnaire import
            logger.warning(f"Validation failed for imported questionnaire {questionnaire.id}: {e}")
        
        # Check if Blue Line exists and perform comparison
        from app.models.blue_line import BlueLine
        blue_line = db.query(BlueLine).filter(
            BlueLine.material_id == material.id
        ).first()
        
        comparison_result = None
        if blue_line:
            # Perform material-specific comparison
            comparison_result = MaterialSupplierComparisonService.compare_questionnaire_with_blue_line(
                questionnaire, blue_line
            )
        else:
            # No Blue Line exists
            comparison_result = ComparisonResult(
                blue_line_exists=False,
                matches=0,
                mismatches=[],
                score=0,
                message="No Blue Line exists for this material. You can create one from this questionnaire."
            )
        
        # Return questionnaire with comparison result in a dict
        # Serialize datetime to ISO string format
        created_at_str = questionnaire.created_at.isoformat() if questionnaire.created_at else None
        
        questionnaire_dict = {
            "id": questionnaire.id,
            "material_id": questionnaire.material_id,
            "supplier_code": questionnaire.supplier_code,
            "questionnaire_type": questionnaire.questionnaire_type.value,
            "version": questionnaire.version,
            "status": questionnaire.status.value,
            "created_at": created_at_str,
            "comparison": comparison_result.model_dump() if comparison_result else None
        }
        
        return questionnaire_dict
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON format: {str(e)}"
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error importing questionnaire: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error importing questionnaire: {str(e)}"
        )


@router.post("/{questionnaire_id}/create-blue-line", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_blue_line_from_questionnaire(
    questionnaire_id: int,
    create_composite: bool = False,
    db: Session = Depends(get_db)
):
    """
    Create a Blue Line from an imported questionnaire.
    
    This is used when no Blue Line exists for the material.
    The questionnaire responses become the Blue Line baseline.
    Also creates a MaterialSupplier automatically.
    """
    from app.models.questionnaire import Questionnaire
    from app.models.material import Material
    from app.models.blue_line import BlueLine, BlueLineMaterialType, BlueLineSyncStatus
    from app.models.questionnaire_template import QuestionnaireTemplate, TemplateType
    from app.services.blue_line_calculator import BlueLineCalculator
    from app.models.composite import Composite, CompositeStatus
    from app.models.material_supplier import MaterialSupplier
    
    questionnaire = db.query(Questionnaire).filter(Questionnaire.id == questionnaire_id).first()
    if not questionnaire:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Questionnaire {questionnaire_id} not found"
        )
    
    material = db.query(Material).filter(Material.id == questionnaire.material_id).first()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Material {questionnaire.material_id} not found"
        )
    
    # Check if Blue Line already exists
    existing_blue_line = db.query(BlueLine).filter(BlueLine.material_id == material.id).first()
    if existing_blue_line:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Blue Line already exists for material {material.reference_code} (ID: {existing_blue_line.id})"
        )
    
    # Get default template
    default_template = db.query(QuestionnaireTemplate).filter(
        QuestionnaireTemplate.is_default == True,
        QuestionnaireTemplate.template_type == TemplateType.INITIAL_HOMOLOGATION
    ).first()
    
    # Determine material type (default to Z001)
    material_type = BlueLineMaterialType.Z001
    
    # Extract responses from questionnaire
    responses = questionnaire.responses.copy() if questionnaire.responses else {}
    
    # Remove metadata fields
    responses_clean = {k: v for k, v in responses.items() if not k.startswith("_")}
    
    # Create empty composite first
    calculator = BlueLineCalculator(db)
    composite = calculator._create_empty_composite(material.id)
    
    # Create Blue Line
    blue_line = BlueLine(
        material_id=material.id,
        template_id=default_template.id if default_template else questionnaire.template_id,
        responses=responses_clean,
        material_type=material_type,
        composite_id=composite.id,
        sync_status=BlueLineSyncStatus.PENDING,
        calculation_metadata={
            "source": "questionnaire_import",
            "questionnaire_id": questionnaire_id,
            "created_from": "imported_questionnaire",
            "date_established": datetime.utcnow().isoformat()
        }
    )
    
    db.add(blue_line)
    db.flush()
    
    # Extract supplier name from questionnaire
    supplier_name = None
    if questionnaire.responses:
        supplier_field = questionnaire.responses.get("q3t1s2f15")
        if supplier_field:
            if isinstance(supplier_field, dict):
                supplier_name = supplier_field.get("value", "")
            else:
                supplier_name = str(supplier_field)
    
    # Check if MaterialSupplier already exists for this material + supplier_code
    # This prevents duplicates when creating Blue Line from multiple questionnaires
    existing_material_supplier = db.query(MaterialSupplier).filter(
        MaterialSupplier.material_id == material.id,
        MaterialSupplier.supplier_code == questionnaire.supplier_code,
        MaterialSupplier.status == "ACTIVE"
    ).first()
    
    # Check if MaterialSupplier already exists for this questionnaire
    existing_for_questionnaire = db.query(MaterialSupplier).filter(
        MaterialSupplier.questionnaire_id == questionnaire.id
    ).first()
    
    if existing_for_questionnaire:
        # MaterialSupplier already exists for this questionnaire - use it
        logger.info(
            f"MaterialSupplier already exists for questionnaire {questionnaire_id} (ID: {existing_for_questionnaire.id}). "
            f"Updating with new blue_line {blue_line.id}."
        )
        existing_for_questionnaire.blue_line_id = blue_line.id
        existing_for_questionnaire.supplier_name = supplier_name
        existing_for_questionnaire.validation_score = 100
        existing_for_questionnaire.mismatch_fields = []
        existing_for_questionnaire.accepted_mismatches = []
        existing_for_questionnaire.validated_at = datetime.utcnow()
        material_supplier = existing_for_questionnaire
    elif existing_material_supplier:
        # MaterialSupplier exists for this material + supplier but different questionnaire
        # This means we're creating a Blue Line from a new questionnaire version
        # We should NOT create a duplicate - just use the existing one
        logger.warning(
            f"MaterialSupplier already exists for material {material.reference_code} "
            f"and supplier {questionnaire.supplier_code} (ID: {existing_material_supplier.id}, "
            f"questionnaire_id: {existing_material_supplier.questionnaire_id}). "
            f"Not creating duplicate for questionnaire {questionnaire_id}. "
            f"Using existing MaterialSupplier."
        )
        # Update the existing MaterialSupplier to reference the new blue_line
        existing_material_supplier.blue_line_id = blue_line.id
        existing_material_supplier.supplier_name = supplier_name
        existing_material_supplier.validation_score = 100
        existing_material_supplier.validated_at = datetime.utcnow()
        material_supplier = existing_material_supplier
    else:
        # Create new MaterialSupplier
        material_supplier = MaterialSupplier(
            material_id=material.id,
            questionnaire_id=questionnaire.id,
            blue_line_id=blue_line.id,
            supplier_code=questionnaire.supplier_code,
            supplier_name=supplier_name,
            status="ACTIVE",
            validation_score=100,  # Perfect match since Blue Line created from this questionnaire
            mismatch_fields=[],
            accepted_mismatches=[],
            validated_at=datetime.utcnow()
        )
        db.add(material_supplier)
    
    # Update questionnaire status
    questionnaire.status = QuestionnaireStatus.APPROVED
    questionnaire.approved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(blue_line)
    db.refresh(material_supplier)
    
    result = {
        "blue_line_id": blue_line.id,
        "material_id": material.id,
        "material_code": material.reference_code,
        "composite_id": composite.id,
        "material_supplier_id": material_supplier.id,
        "message": "Blue Line created successfully from questionnaire"
    }
    
    return result

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


# ===== NEW AI WORKFLOWS =====

@router.post("/{questionnaire_id}/validate-coherence", response_model=dict)
async def validate_coherence(
    questionnaire_id: int,
    db: Session = Depends(get_db)
):
    """
    Validate questionnaire coherence using AI.
    Checks for logical contradictions between related fields.
    """
    from app.services.questionnaire_coherence_validator import QuestionnaireCoherenceValidator
    
    validator = QuestionnaireCoherenceValidator(db)
    try:
        score, issues = validator.validate_coherence(questionnaire_id)
        
        return {
            "questionnaire_id": questionnaire_id,
            "coherence_score": score,
            "issues": issues,
            "status": "validated"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error validating coherence: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating coherence: {str(e)}"
        )


@router.post("/{questionnaire_id}/upload-documents", response_model=dict)
async def upload_documents(
    questionnaire_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload documents (PDFs) for composite extraction.
    Stores document metadata in questionnaire.
    """
    questionnaire = db.query(Questionnaire).filter(
        Questionnaire.id == questionnaire_id
    ).first()
    
    if not questionnaire:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Questionnaire {questionnaire_id} not found"
        )
    
    # Create upload directory
    upload_dir = Path(settings.UPLOAD_DIR) / "questionnaires" / str(questionnaire_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    uploaded_files = []
    
    for file in files:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only PDF files are supported, got {file.filename}"
            )
        
        # Save file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = upload_dir / safe_filename
        
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        uploaded_files.append({
            "filename": file.filename,
            "path": str(file_path),
            "upload_date": datetime.utcnow().isoformat(),
            "type": "pdf"
        })
    
    # Update questionnaire
    if questionnaire.attached_documents is None:
        questionnaire.attached_documents = []
    
    questionnaire.attached_documents.extend(uploaded_files)
    db.commit()
    
    return {
        "questionnaire_id": questionnaire_id,
        "uploaded_files": uploaded_files,
        "total_documents": len(questionnaire.attached_documents)
    }


@router.post("/{questionnaire_id}/extract-composite", response_model=dict)
async def extract_composite(
    questionnaire_id: int,
    db: Session = Depends(get_db)
):
    """
    Extract composite from uploaded documents using AI.
    Creates a Z1 composite from PDFs.
    """
    from app.services.composite_extractor_ai import CompositeExtractorAI
    from app.models.composite import Composite, CompositeComponent, CompositeOrigin, CompositeStatus, CompositeType
    
    questionnaire = db.query(Questionnaire).filter(
        Questionnaire.id == questionnaire_id
    ).first()
    
    if not questionnaire:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Questionnaire {questionnaire_id} not found"
        )
    
    # Check if documents are attached
    if questionnaire.attached_documents is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No documents attached to questionnaire. Please upload PDF documents first."
        )
    
    if not isinstance(questionnaire.attached_documents, list) or len(questionnaire.attached_documents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No documents attached to questionnaire. Please upload PDF documents first."
        )
    
    # Extract PDF paths and validate they exist
    pdf_paths = []
    missing_files = []
    
    for doc in questionnaire.attached_documents:
        if doc.get("type") == "pdf":
            doc_path = Path(doc["path"])
            # Resolve absolute path
            if not doc_path.is_absolute():
                # Try to resolve relative to UPLOAD_DIR
                doc_path = Path(settings.UPLOAD_DIR) / doc["path"]
            
            if doc_path.exists():
                pdf_paths.append(str(doc_path.resolve()))
            else:
                missing_files.append(doc["path"])
                logger.warning(f"PDF file not found: {doc_path} (stored as: {doc['path']})")
    
    if not pdf_paths:
        error_msg = "No PDF documents found"
        if missing_files:
            error_msg += f". Missing files: {', '.join(missing_files)}"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    logger.info(f"Extracting composite from {len(pdf_paths)} PDF(s): {[Path(p).name for p in pdf_paths]}")
    
    # Extract composite - Use OpenAI if configured, otherwise use OCR
    try:
        if settings.USE_OPENAI_FOR_EXTRACTION and settings.OPENAI_API_KEY:
            # Use OpenAI Vision API (more accurate)
            from app.services.composite_extractor_openai import CompositeExtractorOpenAI
            extractor = CompositeExtractorOpenAI(api_key=settings.OPENAI_API_KEY)
            components, confidence = extractor.extract_from_pdfs(pdf_paths, use_vision=True)
            extraction_method = "OPENAI_VISION"
        else:
            # Use OCR-based extraction (local, no API needed)
            from app.services.composite_extractor_ai import CompositeExtractorAI
            extractor = CompositeExtractorAI()
            components, confidence = extractor.extract_from_pdfs(pdf_paths)
            extraction_method = "AI_OCR"
        
        if not components:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No components could be extracted from documents"
            )
        
        # Create composite
        composite = Composite(
            material_id=questionnaire.material_id,
            version=1,  # Will be updated if needed
            origin=CompositeOrigin.CALCULATED,
            composite_type=CompositeType.Z1,
            status=CompositeStatus.DRAFT,
            questionnaire_id=questionnaire_id,
            source_documents=questionnaire.attached_documents,
            extraction_confidence=confidence,
            composite_metadata={
                "extraction_method": extraction_method,
                "extraction_date": datetime.utcnow().isoformat(),
                "source_questionnaire": questionnaire_id
            },
            notes=f"Extracted from {len(pdf_paths)} document(s) with {confidence:.1f}% confidence"
        )
        
        # Add components (validate required fields)
        for comp_data in components:
            # Validate required fields
            if not comp_data.get('component_name'):
                logger.warning(f"Skipping component without name: {comp_data}")
                continue
            
            component = CompositeComponent(
                cas_number=comp_data.get('cas_number') or None,
                component_name=comp_data['component_name'],
                percentage=comp_data.get('percentage', 0.0),
                confidence_level=comp_data.get('confidence', confidence)
            )
            composite.components.append(component)
        
        db.add(composite)
        db.commit()
        db.refresh(composite)
        
        return {
            "questionnaire_id": questionnaire_id,
            "composite_id": composite.id,
            "composite_type": "Z1",
            "components_count": len(components),
            "extraction_confidence": confidence,
            "status": "extracted"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error extracting composite: {e}", exc_info=True)
        import traceback
        error_details = traceback.format_exc()
        logger.debug(f"Full traceback: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting composite: {str(e)}"
        )


@router.get("/{questionnaire_id}/composite", response_model=dict)
def get_questionnaire_composite(
    questionnaire_id: int,
    db: Session = Depends(get_db)
):
    """
    Get composite associated with questionnaire.
    """
    from app.models.composite import Composite
    
    composite = db.query(Composite).filter(
        Composite.questionnaire_id == questionnaire_id
    ).first()
    
    if not composite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No composite found for questionnaire {questionnaire_id}"
        )
    
    return {
        "composite_id": composite.id,
        "composite_type": composite.composite_type.value if composite.composite_type else None,
        "version": composite.version,
        "status": composite.status.value,
        "extraction_confidence": composite.extraction_confidence,
        "components_count": len(composite.components),
        "created_at": composite.created_at.isoformat() if composite.created_at else None
    }

