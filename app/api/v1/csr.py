from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.session import get_db
from app.models.study import Study
from app.models.csr import CsrDocument, CsrSection, CsrSectionVersion
from app.models.template import Template
from app.schemas.csr import (
    CsrDocumentRead,
    CsrSectionRead,
    CsrSectionVersionCreate,
    CsrSectionVersionRead,
    ApplyTemplateRequest,
)
from app.services.csr_defaults import ensure_csr_document_with_default_sections
from app.services.template_context import build_template_context
from app.services.template_renderer import render_template_content
from app.services.docx_export import export_csr_to_docx
from app.deps.auth import get_current_active_user
from app.deps.study_access import get_study_for_user_or_403, verify_study_access
from app.models.user import User

router = APIRouter(prefix="/csr", tags=["csr"])


@router.get("/{study_id}", response_model=CsrDocumentRead)
def get_csr_document(
    study_id: int,
    db: Session = Depends(get_db),
    study: Study = Depends(get_study_for_user_or_403),
):
    """
    Get CSR document for a study.
    
    If the study doesn't exist, returns 404.
    If the CSR document doesn't exist, it will be created with default sections.
    """
    
    # Ensure CSR document exists with default sections
    # Use study title for the CSR document title
    document = ensure_csr_document_with_default_sections(
        db=db,
        study_id=study_id,
        title=f"CSR for {study.title}"
    )
    
    return document


@router.get("/{study_id}/sections", response_model=List[CsrSectionRead])
def get_csr_sections(
    study_id: int,
    db: Session = Depends(get_db),
    study: Study = Depends(get_study_for_user_or_403),
):
    """
    Get all sections for the CSR document of a study.
    
    If the study doesn't exist, returns 404.
    If the CSR document doesn't exist, it will be created with default sections.
    """
    
    # Ensure CSR document exists with default sections
    document = ensure_csr_document_with_default_sections(
        db=db,
        study_id=study_id,
        title=f"CSR for {study.title}"
    )
    
    # Return sections (ordered by order_index from the relationship)
    return document.sections


@router.get("/sections/{section_id}/versions/latest", response_model=CsrSectionVersionRead)
def get_latest_section_version(
    section_id: int,
    db: Session = Depends(get_db),
):
    """
    Get the latest version of a CSR section.
    
    If the section doesn't exist, returns 404.
    If no versions exist, returns 404.
    """
    # Find section by section_id
    section = db.query(CsrSection).filter(CsrSection.id == section_id).first()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found"
        )
    
    # Get latest version (ordered by created_at desc, then id desc as fallback)
    latest_version = (
        db.query(CsrSectionVersion)
        .filter(CsrSectionVersion.section_id == section_id)
        .order_by(desc(CsrSectionVersion.created_at), desc(CsrSectionVersion.id))
        .first()
    )
    
    if not latest_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No versions found for this section"
        )
    
    return latest_version


@router.post(
    "/sections/{section_id}/versions",
    response_model=CsrSectionVersionRead,
    status_code=status.HTTP_201_CREATED
)
def create_section_version(
    section_id: int,
    version_in: CsrSectionVersionCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new version for a CSR section.
    
    If the section doesn't exist, returns 404.
    Creates a new version with source="human".
    """
    # Verify that the section exists
    section = db.query(CsrSection).filter(CsrSection.id == section_id).first()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found"
        )
    
    # Create new version
    version = CsrSectionVersion(
        section_id=section_id,
        text=version_in.text,
        created_by=version_in.created_by,
        source="human",
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    
    return version


@router.post(
    "/sections/{section_id}/apply-template",
    response_model=CsrSectionVersionRead,
    status_code=status.HTTP_201_CREATED
)
def apply_template_to_section(
    section_id: int,
    body: ApplyTemplateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Apply a text template to a CSR section.
    
    Ensures that the section exists and belongs to the study_id from the request.
    Loads the template, builds context from study data, renders the template,
    and creates a new CsrSectionVersion with the rendered text.
    """
    # Verify user has access to the study (study_id is in request body)
    verify_study_access(body.study_id, current_user.id, db)
    
    # Verify that the section exists
    section = db.query(CsrSection).filter(CsrSection.id == section_id).first()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found"
        )
    
    # Verify that the section belongs to the study_id from the request
    document = db.query(CsrDocument).filter(CsrDocument.id == section.document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CSR document not found for this section"
        )
    
    if document.study_id != body.study_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Section does not belong to the specified study"
        )
    
    # Load template by template_id
    template = db.query(Template).filter(Template.id == body.template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Build context using the generic helper (same as /templates/{id}/render)
    try:
        context = build_template_context(
            db, 
            study_id=body.study_id, 
            extra_context=body.extra_context or {}
        )
    except ValueError as e:
        # build_template_context raises ValueError if study not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    # Render template
    rendered_text, used_variables, missing_variables = render_template_content(
        template, context
    )
    
    # Create a new CsrSectionVersion with rendered text
    version = CsrSectionVersion(
        section_id=section_id,
        text=rendered_text,
        source="template",
        template_id=template.id,
        created_by=current_user.username,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    
    return version


@router.get("/{study_id}/export/docx")
def export_csr_document_to_docx(
    study_id: int,
    db: Session = Depends(get_db),
    study: Study = Depends(get_study_for_user_or_403),
):
    """
    Export CSR document to DOCX format.
    
    Finds CSRDocument by study_id, exports it to DOCX, and returns the file
    with proper Content-Type and Content-Disposition headers.
    
    If the study doesn't exist, returns 404.
    If the CSR document doesn't exist, it will be created with default sections.
    """
    # Ensure CSR document exists with default sections
    document = ensure_csr_document_with_default_sections(
        db=db,
        study_id=study_id,
        title=f"CSR for {study.title}"
    )
    
    # Export to DOCX
    try:
        docx_bytes = export_csr_to_docx(document.id, db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    # Generate filename
    filename = f"csr_{study.code or study_id}.docx"
    
    # Return file with proper headers
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
