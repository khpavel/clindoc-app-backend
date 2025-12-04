from sqlalchemy.orm import Session

from app.models.csr import CsrDocument, CsrSection


DEFAULT_CSR_SECTIONS = [
    {"code": "SYNOPSIS", "title": "Synopsis"},
    {"code": "EFFICACY", "title": "Efficacy Results"},
    {"code": "SAFETY", "title": "Safety Results"},
    {"code": "PK", "title": "Pharmacokinetics"},
    {"code": "DISCUSSION", "title": "Discussion"},
]


def ensure_csr_document_with_default_sections(
    db: Session,
    study_id: int,
    title: str | None = None,
) -> CsrDocument:
    """
    Ensure a CSR document exists for the given study_id with default sections.
    
    If the document doesn't exist, create it. If it exists but has no sections,
    create default sections from DEFAULT_CSR_SECTIONS.
    
    Args:
        db: Database session
        study_id: ID of the study
        title: Optional title for the document. If not provided and document
               is created, defaults to "CSR for study {study_id}"
    
    Returns:
        The CsrDocument instance (existing or newly created)
    """
    # Try to find existing CsrDocument for study_id
    document = db.query(CsrDocument).filter(CsrDocument.study_id == study_id).first()
    
    if not document:
        # Create a new document with title or default
        document_title = title or f"CSR for study {study_id}"
        document = CsrDocument(
            study_id=study_id,
            title=document_title,
            status="draft",
        )
        db.add(document)
        db.flush()  # Flush to get the document ID
    
    # If the document has no sections, create default sections
    if not document.sections:
        for index, section_data in enumerate(DEFAULT_CSR_SECTIONS, start=1):
            section = CsrSection(
                document_id=document.id,
                code=section_data["code"],
                title=section_data["title"],
                order_index=index,
            )
            db.add(section)
    
    # Commit changes
    db.commit()
    db.refresh(document)
    
    return document

