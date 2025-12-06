from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.study import Study
from app.models.document import Document
from app.schemas.output_document import (
    CsrDocumentRead,
    CsrSectionRead,
    CsrSectionVersionCreate,
    CsrSectionVersionRead,
    ApplyTemplateRequest,
)
from app.deps.auth import get_current_active_user
from app.deps.study_access import get_study_for_user_or_403
from app.models.user import User

# Import endpoint functions from output router to reuse logic (with aliases to avoid name conflicts)
from app.api.v1.output import (
    get_output_document_by_document_id as _get_output_document_by_document_id,
    get_output_document as _get_output_document,
    get_output_sections as _get_output_sections,
    get_latest_section_version as _get_latest_section_version,
    create_section_version as _create_section_version,
    apply_template_to_section as _apply_template_to_section,
    export_output_document_to_docx as _export_output_document_to_docx,
    get_document_for_user_or_403,
)

router = APIRouter(prefix="/csr", tags=["csr"])


@router.get("/document/{document_id}", response_model=CsrDocumentRead, deprecated=True)
def get_csr_document_by_document_id(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    document: Document = Depends(get_document_for_user_or_403),
):
    """
    Get CSR document by Document ID.
    
    **DEPRECATED**: This endpoint is deprecated. Use `GET /api/v1/output/document/{document_id}` instead.
    This endpoint will be removed in a future major version.
    
    Loads the Document by ID, ensures user has access to its study,
    checks that document.type == "csr", and returns the linked OutputDocument.
    If the OutputDocument doesn't exist, it will be created with default sections.
    
    Error Responses:
    - 400: Document type is not "csr"
    - 403: User is not a member of the study
    - 404: Document or study not found
    """
    # Delegate to output router endpoint
    return _get_output_document_by_document_id(document_id, db, current_user, document)


@router.get("/{study_id}", response_model=CsrDocumentRead, deprecated=True)
def get_csr_document(
    study_id: int,
    db: Session = Depends(get_db),
    study: Study = Depends(get_study_for_user_or_403),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get CSR document for a study.
    
    **DEPRECATED**: This endpoint is deprecated. Use `GET /api/v1/output/{study_id}` instead.
    This endpoint will be removed in a future major version.
    
    If the study doesn't exist, returns 404.
    If the Output Document doesn't exist, it will be created with default sections.
    Uses the normalized OutputDocument loading function to ensure consistency with document-based endpoints.
    """
    # Delegate to output router endpoint
    return _get_output_document(study_id, db, study, current_user)


@router.get("/{study_id}/sections", response_model=List[CsrSectionRead], deprecated=True)
def get_csr_sections(
    study_id: int,
    db: Session = Depends(get_db),
    study: Study = Depends(get_study_for_user_or_403),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get all sections for the CSR document of a study.
    
    **DEPRECATED**: This endpoint is deprecated. Use `GET /api/v1/output/{study_id}/sections` instead.
    This endpoint will be removed in a future major version.
    
    If the study doesn't exist, returns 404.
    If the Output Document doesn't exist, it will be created with default sections.
    Uses the normalized OutputDocument loading function to ensure consistency with document-based endpoints.
    """
    # Delegate to output router endpoint
    return _get_output_sections(study_id, db, study, current_user)


@router.get("/sections/{section_id}/versions/latest", response_model=CsrSectionVersionRead, deprecated=True)
def get_latest_section_version(
    section_id: int,
    db: Session = Depends(get_db),
):
    """
    Get the latest version of a CSR section.
    
    **DEPRECATED**: This endpoint is deprecated. Use `GET /api/v1/output/sections/{section_id}/versions/latest` instead.
    This endpoint will be removed in a future major version.
    
    If the section doesn't exist, returns 404.
    If no versions exist, returns 404.
    """
    # Delegate to output router endpoint
    return _get_latest_section_version(section_id, db)


@router.post(
    "/sections/{section_id}/versions",
    response_model=CsrSectionVersionRead,
    status_code=status.HTTP_201_CREATED,
    deprecated=True
)
def create_section_version(
    section_id: int,
    version_in: CsrSectionVersionCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new version for a CSR section.
    
    **DEPRECATED**: This endpoint is deprecated. Use `POST /api/v1/output/sections/{section_id}/versions` instead.
    This endpoint will be removed in a future major version.
    
    If the section doesn't exist, returns 404.
    Creates a new version with source="human".
    """
    # Delegate to output router endpoint
    return _create_section_version(section_id, version_in, db)


@router.post(
    "/sections/{section_id}/apply-template",
    response_model=CsrSectionVersionRead,
    status_code=status.HTTP_201_CREATED,
    deprecated=True
)
def apply_template_to_section(
    section_id: int,
    body: ApplyTemplateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Apply a text template to a CSR section.
    
    **DEPRECATED**: This endpoint is deprecated. Use `POST /api/v1/output/sections/{section_id}/apply-template` instead.
    This endpoint will be removed in a future major version.
    
    Ensures that the section exists and belongs to the study_id from the request.
    Loads the template, builds context from study data, renders the template,
    and creates a new OutputSectionVersion with the rendered text.
    """
    # Delegate to output router endpoint
    return _apply_template_to_section(section_id, body, db, current_user)


@router.get("/{study_id}/export/docx", deprecated=True)
def export_csr_document_to_docx(
    study_id: int,
    db: Session = Depends(get_db),
    study: Study = Depends(get_study_for_user_or_403),
    current_user: User = Depends(get_current_active_user),
):
    """
    Export CSR document to DOCX format.
    
    **DEPRECATED**: This endpoint is deprecated. Use `GET /api/v1/output/{study_id}/export/docx` instead.
    This endpoint will be removed in a future major version.
    
    Finds OutputDocument by study_id, exports it to DOCX, and returns the file
    with proper Content-Type and Content-Disposition headers.
    
    If the study doesn't exist, returns 404.
    If the Output Document doesn't exist, it will be created with default sections.
    Uses the normalized OutputDocument loading function to ensure consistency with document-based endpoints.
    """
    # Delegate to output router endpoint
    return _export_output_document_to_docx(study_id, db, study, current_user)
