from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.template import Template
from app.models.study import Study
from app.schemas.template import (
    TemplateRead,
    TemplateRenderRequest,
    TemplateRenderResponse,
)
from app.services.template_renderer import render_template_content

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("/section/{section_code}", response_model=List[TemplateRead])
def get_templates_by_section(
    section_code: str,
    language: Optional[str] = None,
    scope: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Get templates for a specific section code.
    
    Filters by:
    - type="section_text"
    - matching section_code
    - optional language filter
    - optional scope filter
    - is_active = True
    """
    query = db.query(Template).filter(
        Template.type == "section_text",
        Template.section_code == section_code,
        Template.is_active == True,
    )
    
    if language is not None:
        query = query.filter(Template.language == language)
    
    if scope is not None:
        query = query.filter(Template.scope == scope)
    
    templates = query.all()
    return templates


@router.post("/{template_id}/render", response_model=TemplateRenderResponse)
def render_template(
    template_id: int,
    request: TemplateRenderRequest,
    db: Session = Depends(get_db),
):
    """
    Render a template with the provided context.
    
    Loads the template by id, builds a context from the study data,
    and renders the template content.
    """
    # Load template by id
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Load study by study_id
    study = db.query(Study).filter(Study.id == request.study_id).first()
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Build context dict
    context = {
        "study_code": study.code,
        "study_title": study.title,
        "study_phase": study.phase,
    }
    
    # Merge with extra_context if provided
    if request.extra_context:
        context.update(request.extra_context)
    
    # Render template
    rendered_text, used_variables, missing_variables = render_template_content(
        template, context
    )
    
    return TemplateRenderResponse(
        rendered_text=rendered_text,
        used_variables=used_variables if used_variables else None,
        missing_variables=missing_variables if missing_variables else None,
    )

