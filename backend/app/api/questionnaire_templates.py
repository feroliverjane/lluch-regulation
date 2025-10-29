from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.questionnaire_template import QuestionnaireTemplate, TemplateType
from pydantic import BaseModel


router = APIRouter(prefix="/questionnaire-templates", tags=["questionnaire-templates"])


# Schemas
class QuestionnaireTemplateResponse(BaseModel):
    id: int
    name: str
    description: str | None
    template_type: str
    version: str
    questions_schema: list
    total_questions: int | None
    total_sections: int | None
    is_active: bool
    is_default: bool

    class Config:
        from_attributes = True


@router.get("", response_model=List[QuestionnaireTemplateResponse])
def list_templates(
    template_type: TemplateType | None = None,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """List all questionnaire templates"""
    query = db.query(QuestionnaireTemplate)
    
    if template_type:
        query = query.filter(QuestionnaireTemplate.template_type == template_type)
    
    if active_only:
        query = query.filter(QuestionnaireTemplate.is_active == True)
    
    templates = query.order_by(QuestionnaireTemplate.created_at.desc()).all()
    
    return templates


@router.get("/default", response_model=QuestionnaireTemplateResponse)
def get_default_template(db: Session = Depends(get_db)):
    """Get the default template"""
    template = db.query(QuestionnaireTemplate).filter(
        QuestionnaireTemplate.is_default == True,
        QuestionnaireTemplate.is_active == True
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No default template found"
        )
    
    return template


@router.get("/{template_id}", response_model=QuestionnaireTemplateResponse)
def get_template(template_id: int, db: Session = Depends(get_db)):
    """Get a specific template"""
    template = db.query(QuestionnaireTemplate).filter(
        QuestionnaireTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found"
        )
    
    return template


@router.get("/{template_id}/sections", response_model=dict)
def get_template_sections(template_id: int, db: Session = Depends(get_db)):
    """Get template questions organized by sections"""
    template = db.query(QuestionnaireTemplate).filter(
        QuestionnaireTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found"
        )
    
    # Organize questions by tab and section
    organized = {}
    for question in template.questions_schema:
        tab = question.get("tab", 0)
        section = question.get("section", 0)
        
        tab_key = f"Tab_{tab}"
        section_key = f"Section_{section}"
        
        if tab_key not in organized:
            organized[tab_key] = {}
        
        if section_key not in organized[tab_key]:
            organized[tab_key][section_key] = []
        
        organized[tab_key][section_key].append(question)
    
    return {
        "template_id": template.id,
        "template_name": template.name,
        "total_tabs": len(organized),
        "total_sections": sum(len(sections) for sections in organized.values()),
        "sections": organized
    }

