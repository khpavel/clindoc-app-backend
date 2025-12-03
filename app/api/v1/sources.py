from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.source import SourceDocument
from app.models.study import Study
from app.schemas.source import SourceDocumentRead

router = APIRouter()

# Storage directory relative to project root
STORAGE_DIR = Path("storage")


@router.post("/sources/{study_id}/upload", response_model=SourceDocumentRead)
async def upload_source_document(
    study_id: int,
    file: UploadFile = File(...),
    type: str = Form(...),
    db: Session = Depends(get_db),
):
    # Verify that the study exists
    study = db.query(Study).filter(Study.id == study_id).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")

    # Create storage directory if it doesn't exist
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    # Generate a unique filename to avoid conflicts
    file_extension = Path(file.filename).suffix
    file_name = file.filename
    storage_path = STORAGE_DIR / file_name

    # Handle filename conflicts by appending a number
    counter = 1
    while storage_path.exists():
        name_without_ext = Path(file.filename).stem
        file_name = f"{name_without_ext}_{counter}{file_extension}"
        storage_path = STORAGE_DIR / file_name
        counter += 1

    # Save the file
    try:
        with open(storage_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Create SourceDocument record with relative path
    source_doc = SourceDocument(
        study_id=study_id,
        type=type,
        file_name=file_name,
        storage_path=str(storage_path),  # Relative to project root
    )
    db.add(source_doc)
    db.commit()
    db.refresh(source_doc)

    return source_doc


@router.get("/sources/{study_id}", response_model=List[SourceDocumentRead])
def list_source_documents(
    study_id: int,
    db: Session = Depends(get_db),
):
    # Verify that the study exists
    study = db.query(Study).filter(Study.id == study_id).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")

    # Get all source documents for the study
    source_documents = db.query(SourceDocument).filter(
        SourceDocument.study_id == study_id
    ).order_by(SourceDocument.uploaded_at.desc()).all()

    return source_documents

