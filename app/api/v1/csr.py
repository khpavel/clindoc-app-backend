from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.csr import CsrSection, CsrSectionVersion
from app.schemas.csr import CsrSectionVersionCreate, CsrSectionVersionRead

router = APIRouter()


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
