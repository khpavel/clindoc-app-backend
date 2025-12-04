from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.csr import CsrDocument, CsrSection, CsrSectionVersion
from app.schemas.csr import CsrDocumentRead, CsrSectionVersionCreate, CsrSectionVersionRead

router = APIRouter()


@router.get("/csr/{document_id}", response_model=CsrDocumentRead)
def get_csr_document(
    document_id: int,
    db: Session = Depends(get_db),
):
    """Get a CSR document by ID with its sections."""
    document = db.query(CsrDocument).filter(CsrDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Not Found")
    return document


@router.post("/csr/sections/{section_id}/versions", response_model=CsrSectionVersionRead)
def create_section_version(
    section_id: int,
    version_in: CsrSectionVersionCreate,
    db: Session = Depends(get_db),
):
    # Verify that the section exists
    section = db.query(CsrSection).filter(CsrSection.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    # Create new version
    version = CsrSectionVersion(
        section_id=section_id,
        text=version_in.text,
        created_by=version_in.created_by,
        source="human",
        created_at=datetime.utcnow(),
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version
