from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.session import get_db
from app.models.study import Study
from app.models.csr import CsrDocument, CsrSection, CsrSectionVersion
from app.models.document import Document
from app.models.template import Template
from app.schemas.csr import (
    CsrDocumentRead,
    CsrSectionRead,
    CsrSectionVersionCreate,
    CsrSectionVersionRead,
    ApplyTemplateRequest,
)
from app.services.csr_document_link import get_or_create_csr_for_document, get_or_create_csr_for_study
from app.services.template_context import build_template_context
from app.services.template_renderer import render_template_content
from app.services.docx_export import export_csr_to_docx
from app.deps.auth import get_current_active_user
from app.deps.study_access import get_study_for_user_or_403, verify_study_access
from app.models.user import User

router = APIRouter(prefix="/csr", tags=["csr"])


def get_document_for_user_or_403(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Document:
    """
    Dependency that verifies the current user has access to the document.
    
    Checks if the document exists and if the user is a member of the document's study.
    Returns the Document if access is granted, raises 403/404 if not.
    
    Use this as a dependency for endpoints where document_id is a path parameter.
    """
    # Find the document
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Verify user has access to the study
    verify_study_access(document.study_id, current_user.id, db)
    
    return document


@router.get("/document/{document_id}", response_model=CsrDocumentRead)
def get_csr_document_by_document_id(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    document: Document = Depends(get_document_for_user_or_403),
):
    """
    Get CSR document by Document ID.
    
    Loads the Document by ID, ensures user has access to its study,
    checks that document.type == "csr", and returns the linked CSRDocument.
    If the CSRDocument doesn't exist, it will be created with default sections.
    
    Error Responses:
    - 400: Document type is not "csr"
    - 403: User is not a member of the study
    - 404: Document or study not found
    """
    # Check that document type is "csr"
    if document.type != "csr":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document type must be 'csr', got '{document.type}'"
        )
    
    # Get or create CSRDocument for this document
    try:
        csr_document = get_or_create_csr_for_document(document, current_user, db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return csr_document


@router.get("/{study_id}", response_model=CsrDocumentRead)
def get_csr_document(
    study_id: int,
    db: Session = Depends(get_db),
    study: Study = Depends(get_study_for_user_or_403),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get CSR document for a study.
    
    If the study doesn't exist, returns 404.
    If the CSR document doesn't exist, it will be created with default sections.
    Uses the normalized CSR loading function to ensure consistency with document-based endpoints.
    """
    
    # Use normalized function that finds/creates Document and CSRDocument
    csr_document = get_or_create_csr_for_study(
        study_id=study_id,
        user=current_user,
        db=db,
        title=f"CSR for {study.title}"
    )
    
    return csr_document


@router.get("/{study_id}/sections", response_model=List[CsrSectionRead])
def get_csr_sections(
    study_id: int,
    db: Session = Depends(get_db),
    study: Study = Depends(get_study_for_user_or_403),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get all sections for the CSR document of a study.
    
    If the study doesn't exist, returns 404.
    If the CSR document doesn't exist, it will be created with default sections.
    Uses the normalized CSR loading function to ensure consistency with document-based endpoints.
    """
    
    # Use normalized function that finds/creates Document and CSRDocument
    csr_document = get_or_create_csr_for_study(
        study_id=study_id,
        user=current_user,
        db=db,
        title=f"CSR for {study.title}"
    )
    
    # Return sections (ordered by order_index from the relationship)
    return csr_document.sections


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
    current_user: User = Depends(get_current_active_user),
):
    """
    Export CSR document to DOCX format.
    
    Finds CSRDocument by study_id, exports it to DOCX, and returns the file
    with proper Content-Type and Content-Disposition headers.
    
    If the study doesn't exist, returns 404.
    If the CSR document doesn't exist, it will be created with default sections.
    Uses the normalized CSR loading function to ensure consistency with document-based endpoints.
    """
    # Use normalized function that finds/creates Document and CSRDocument
    csr_document = get_or_create_csr_for_study(
        study_id=study_id,
        user=current_user,
        db=db,
        title=f"CSR for {study.title}"
    )
    
    # Export to DOCX
    try:
        docx_bytes = export_csr_to_docx(csr_document.id, db)
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
