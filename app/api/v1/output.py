from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.session import get_db
from app.models.study import Study
from app.models.output_document import OutputDocument, OutputSection, OutputSectionVersion
from app.models.document import Document
from app.models.template import Template
from app.schemas.output_document import (
    OutputDocumentRead,
    OutputSectionRead,
    OutputSectionVersionCreate,
    OutputSectionVersionRead,
    ApplyTemplateRequest,
)
from app.services.output_document_document_link import get_or_create_output_document_for_document, get_or_create_output_document_for_study
from app.services.template_context import build_template_context
from app.services.template_renderer import render_template_content
from app.services.docx_export import export_csr_to_docx
from app.services.language_resolver import resolve_content_language
from app.deps.auth import get_current_active_user
from app.deps.study_access import get_study_for_user_or_403, verify_study_access
from app.deps.language import get_request_language
from app.models.user import User

router = APIRouter(prefix="/output", tags=["output"])


def get_document_for_user_or_403(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    language: str = Depends(get_request_language),
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
    verify_study_access(document.study_id, current_user.id, db, language=language)
    
    return document


@router.get("/document/{document_id}", response_model=OutputDocumentRead)
def get_output_document_by_document_id(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    document: Document = Depends(get_document_for_user_or_403),
    language: str = Depends(get_request_language),
):
    """
    Get Output Document by Document ID.
    
    Loads the Document by ID, ensures user has access to its study,
    checks that document.type == "csr", and returns the linked OutputDocument.
    If the OutputDocument doesn't exist, it will be created with default sections.
    
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
    
    # Get or create OutputDocument for this document
    try:
        output_document = get_or_create_output_document_for_document(document, current_user, db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return output_document


@router.get("/{study_id}", response_model=OutputDocumentRead)
def get_output_document(
    study_id: int,
    db: Session = Depends(get_db),
    study: Study = Depends(get_study_for_user_or_403),
    current_user: User = Depends(get_current_active_user),
    language: str = Depends(get_request_language),
):
    """
    Get Output Document for study.
    
    If the study doesn't exist, returns 404.
    If the Output Document doesn't exist, it will be created with default sections.
    Uses the normalized OutputDocument loading function to ensure consistency with document-based endpoints.
    """
    
    # Use normalized function that finds/creates Document and OutputDocument
    output_document = get_or_create_output_document_for_study(
        study_id=study_id,
        user=current_user,
        db=db,
        title=f"CSR for {study.title}"
    )
    
    return output_document


@router.get("/{study_id}/sections", response_model=List[OutputSectionRead])
def get_output_sections(
    study_id: int,
    db: Session = Depends(get_db),
    study: Study = Depends(get_study_for_user_or_403),
    current_user: User = Depends(get_current_active_user),
    language: str = Depends(get_request_language),
):
    """
    Get all sections for the Output Document of a study.
    
    If the study doesn't exist, returns 404.
    If the Output Document doesn't exist, it will be created with default sections.
    Uses the normalized OutputDocument loading function to ensure consistency with document-based endpoints.
    """
    
    # Use normalized function that finds/creates Document and OutputDocument
    output_document = get_or_create_output_document_for_study(
        study_id=study_id,
        user=current_user,
        db=db,
        title=f"CSR for {study.title}"
    )
    
    # Return sections (ordered by order_index from the relationship)
    return output_document.sections


@router.get("/sections/{section_id}/versions/latest", response_model=OutputSectionVersionRead)
def get_latest_section_version(
    section_id: int,
    db: Session = Depends(get_db),
):
    """
    Get the latest version of an Output Document section.
    
    If the section doesn't exist, returns 404.
    If no versions exist, returns 404.
    """
    # Find section by section_id
    section = db.query(OutputSection).filter(OutputSection.id == section_id).first()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found"
        )
    
    # Get latest version (ordered by created_at desc, then id desc as fallback)
    latest_version = (
        db.query(OutputSectionVersion)
        .filter(OutputSectionVersion.section_id == section_id)
        .order_by(desc(OutputSectionVersion.created_at), desc(OutputSectionVersion.id))
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
    response_model=OutputSectionVersionRead,
    status_code=status.HTTP_201_CREATED
)
def create_section_version(
    section_id: int,
    version_in: OutputSectionVersionCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new version for an Output Document section.
    
    If the section doesn't exist, returns 404.
    Creates a new version with source="human".
    """
    # Verify that the section exists
    section = db.query(OutputSection).filter(OutputSection.id == section_id).first()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found"
        )
    
    # Create new version
    version = OutputSectionVersion(
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
    response_model=OutputSectionVersionRead,
    status_code=status.HTTP_201_CREATED
)
def apply_template_to_section(
    section_id: int,
    body: ApplyTemplateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    request_language: str = Depends(get_request_language),
):
    """
    Apply a text template to an Output Document section.
    
    Ensures that the section exists and belongs to the study_id from the request.
    Loads the template, builds context from study data, renders the template,
    and creates a new OutputSectionVersion with the rendered text.
    
    Uses the document's content language (if available) for template rendering,
    rather than the UI/request language.
    """
    # Verify user has access to the study (study_id is in request body)
    verify_study_access(body.study_id, current_user.id, db, language=request_language)
    
    # Verify that the section exists
    section = db.query(OutputSection).filter(OutputSection.id == section_id).first()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found"
        )
    
    # Verify that the section belongs to the study_id from the request
    output_document = db.query(OutputDocument).filter(OutputDocument.id == section.document_id).first()
    if not output_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output document not found for this section"
        )
    
    if output_document.study_id != body.study_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Section does not belong to the specified study"
        )
    
    # Get the Document linked to this OutputDocument (if any) to determine content language
    document = None
    if output_document.document_id:
        document = db.query(Document).filter(Document.id == output_document.document_id).first()
    
    # Resolve content language for template rendering
    content_language = resolve_content_language(document, current_user, request_language)
    
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
            extra_context=body.extra_context or {},
            language=content_language,
        )
    except ValueError as e:
        # build_template_context raises ValueError if study not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    # Render template using content language
    rendered_text, used_variables, missing_variables = render_template_content(
        template, context, language=content_language
    )
    
    # Create a new OutputSectionVersion with rendered text
    version = OutputSectionVersion(
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
def export_output_document_to_docx(
    study_id: int,
    db: Session = Depends(get_db),
    study: Study = Depends(get_study_for_user_or_403),
    current_user: User = Depends(get_current_active_user),
    language: str = Depends(get_request_language),
):
    """
    Export Output Document to DOCX format.
    
    Finds OutputDocument by study_id, exports it to DOCX, and returns the file
    with proper Content-Type and Content-Disposition headers.
    
    If the study doesn't exist, returns 404.
    If the Output Document doesn't exist, it will be created with default sections.
    Uses the normalized OutputDocument loading function to ensure consistency with document-based endpoints.
    """
    # Use normalized function that finds/creates Document and OutputDocument
    output_document = get_or_create_output_document_for_study(
        study_id=study_id,
        user=current_user,
        db=db,
        title=f"CSR for {study.title}"
    )
    
    # Export to DOCX
    try:
        docx_bytes = export_csr_to_docx(output_document.id, db)
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

