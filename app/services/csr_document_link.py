from sqlalchemy.orm import Session

from app.models.csr import CsrDocument, CsrSection
from app.models.document import Document
from app.models.user import User
from app.services.csr_defaults import DEFAULT_CSR_SECTIONS


def get_or_create_csr_for_study(study_id: int, user: User, db: Session, title: str | None = None) -> CsrDocument:
    """
    Get or create a CSRDocument for a study by finding/creating a default Document.
    
    This is the normalized entry point for CSR loading that:
    1. Finds or creates a default Document of type "csr" for the study
    2. Then calls get_or_create_csr_for_document to ensure CSRDocument exists
    
    This ensures consistent behavior between:
    - GET /api/v1/csr/{study_id} (study-based)
    - GET /api/v1/csr/document/{document_id} (document-based)
    
    Args:
        study_id: ID of the study
        user: The User instance (for logging/audit purposes)
        db: Database session
        title: Optional title for the Document if creating new. If not provided,
              defaults to "CSR for {study.code}" or "CSR for Study {study_id}"
    
    Returns:
        The CsrDocument instance (existing or newly created)
    """
    # Try to find an existing Document of type "csr" for this study
    document = db.query(Document).filter(
        Document.study_id == study_id,
        Document.type == "csr"
    ).first()
    
    if not document:
        # Create a new Document of type "csr"
        # Try to get study title for better naming
        from app.models.study import Study
        study = db.query(Study).filter(Study.id == study_id).first()
        
        if title is None:
            if study and study.code:
                title = f"CSR for {study.code}"
            elif study and study.title:
                title = f"CSR for {study.title}"
            else:
                title = f"CSR for Study {study_id}"
        
        document = Document(
            study_id=study_id,
            type="csr",
            title=title,
            status="draft",
            created_by=user.id,
        )
        db.add(document)
        db.flush()  # Flush to get the document ID
    
    # Now use the document-based function to ensure CSRDocument exists
    return get_or_create_csr_for_document(document, user, db)


def get_or_create_csr_for_document(document: Document, user: User, db: Session) -> CsrDocument:
    """
    Get or create a CSRDocument linked to a Document.
    
    Ensures that:
    - document.type == "csr"
    - document.study_id exists
    - If document.csr_document already exists, return it
    - Otherwise, create a new CSRDocument with:
      - study_id = document.study_id
      - title = document.title
      - status = document.status (or "draft")
      - document_id = document.id
    - Initialize sections using the same logic as ensure_csr_document_with_default_sections
    
    Args:
        document: The Document instance (must be type "csr")
        user: The User instance (for logging/audit purposes)
        db: Database session
    
    Returns:
        The CsrDocument instance (existing or newly created)
    
    Raises:
        ValueError: If document.type is not "csr" or document.study_id is None
    """
    # Validate document type
    if document.type != "csr":
        raise ValueError(f"Document type must be 'csr', got '{document.type}'")
    
    if document.study_id is None:
        raise ValueError("Document must have a study_id")
    
    # Check if CSRDocument already exists for this document
    if document.csr_document:
        return document.csr_document
    
    # Check if there's already a CSRDocument for this study (legacy case)
    existing_csr = db.query(CsrDocument).filter(CsrDocument.study_id == document.study_id).first()
    if existing_csr:
        # Link the existing CSRDocument to this document
        existing_csr.document_id = document.id
        db.commit()
        db.refresh(existing_csr)
        return existing_csr
    
    # Create a new CSRDocument
    csr_document = CsrDocument(
        study_id=document.study_id,
        title=document.title,
        status=document.status or "draft",
        document_id=document.id,
    )
    db.add(csr_document)
    db.flush()  # Flush to get the document ID
    
    # Create default sections
    for index, section_data in enumerate(DEFAULT_CSR_SECTIONS, start=1):
        section = CsrSection(
            document_id=csr_document.id,
            code=section_data["code"],
            title=section_data["title"],
            order_index=index,
        )
        db.add(section)
    
    # Commit changes
    db.commit()
    db.refresh(csr_document)
    
    return csr_document

