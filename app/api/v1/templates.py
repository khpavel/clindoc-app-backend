from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.template import Template
from app.schemas.template import (
    TemplateRead,
    TemplateRenderRequest,
    TemplateRenderResponse,
)
from app.services.template_context import build_template_context
from app.services.template_renderer import render_template_content
from app.deps.language import get_request_language

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
    body: TemplateRenderRequest,
    db: Session = Depends(get_db),
    language: str = Depends(get_request_language),
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
    
    # Build the base context
    ctx = build_template_context(db, body.study_id, extra_context=body.extra_context or {}, language=language)
    
    # Render template
    rendered_text, used_vars, missing_vars = render_template_content(template, ctx, language=language)
    
    return TemplateRenderResponse(
        rendered_text=rendered_text,
        used_variables=used_vars,
        missing_variables=missing_vars,
    )

