from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps.auth import get_current_active_user
from app.deps.study_access import get_study_for_user_or_403, verify_study_editor_access
from app.models.document import Document
from app.models.study import Study
from app.models.user import User
from app.schemas.document import DocumentCreate, DocumentRead

router = APIRouter(prefix="/studies", tags=["documents"])


def get_or_create_default_csr_document(study_id: int, user: User, db: Session) -> Optional[Document]:
    """
    Helper function to get or create a default CSR document for a study.
    
    Checks if there is already a Document of type "csr" for this study.
    If not, creates one with:
    - title = "CSR for {study.code}" (or "CSR for Study {study_id}" if code is not available)
    - status = "draft"
    - created_by = current user
    
    Returns the existing or newly created Document, or None if study doesn't exist.
    """
    # Get the study to access its code
    study = db.query(Study).filter(Study.id == study_id).first()
    if not study:
        return None
    
    # Check if CSR document already exists
    existing_csr = (
        db.query(Document)
        .filter(Document.study_id == study_id, Document.type == "csr")
        .first()
    )
    
    if existing_csr:
        return existing_csr
    
    # Create default CSR document
    title = f"CSR for {study.code}" if study.code else f"CSR for Study {study_id}"
    default_csr = Document(
        study_id=study_id,
        type="csr",
        title=title,
        status="draft",
        created_by=user.id,
    )
    db.add(default_csr)
    db.commit()
    db.refresh(default_csr)
    return default_csr


@router.get("/{study_id}/documents", response_model=List[DocumentRead])
def list_documents(
    study_id: int,
    ensure_default_csr: bool = Query(False, description="If true, automatically create a default CSR document if none exists"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    study: Study = Depends(get_study_for_user_or_403),
):
    """
    List all documents for a study.
    
    Only study members can view documents.
    Returns documents ordered by type first, then by created_at ascending.
    
    If ensure_default_csr=true, automatically creates a default CSR document
    if one doesn't exist for the study.
    """
    # Optionally ensure default CSR document exists
    if ensure_default_csr:
        get_or_create_default_csr_document(study_id, current_user, db)
    
    # Query documents with deterministic ordering: type first, then created_at ascending
    documents = (
        db.query(Document)
        .filter(Document.study_id == study_id)
        .order_by(Document.type.asc(), Document.created_at.asc())
        .all()
    )
    return documents


@router.post("/{study_id}/documents", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
def create_document(
    study_id: int,
    document_in: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new document for a study.
    
    Only study owners and editors can create documents.
    The document is created with status "draft" by default.
    """
    # Verify user has editor access (owner or editor role)
    verify_study_editor_access(study_id, current_user.id, db)
    
    # Create the document
    document = Document(
        study_id=study_id,
        type=document_in.type,
        title=document_in.title,
        template_code=document_in.template_code,
        status=document_in.status,
        current_version_label=document_in.current_version_label,
        created_by=current_user.id,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document

