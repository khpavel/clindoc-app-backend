import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.storage import build_study_source_path
from app.db.session import get_db
from app.models.source import SourceDocument
from app.models.study import Study
from app.schemas.source import SourceDocumentRead
from app.services.rag_ingest import ingest_source_document_to_rag

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sources", tags=["sources"])

# Optional: Import get_current_active_user if available for future use
try:
    from app.deps.auth import get_current_active_user
    from app.models.user import User
except ImportError:
    get_current_active_user = None
    User = None


@router.post("/{study_id}/upload", response_model=SourceDocumentRead)
async def upload_source_document(
    study_id: int,
    file: UploadFile = File(...),
    type: str = Form(...),
    db: Session = Depends(get_db),
    # Optional: Uncomment when authentication is wired:
    # current_user: Optional[User] = Depends(get_current_active_user) if get_current_active_user else None,
):
    """
    Upload a source document for a study.
    
    - Accepts multipart/form-data with:
      - file: UploadFile - The document file to upload
      - type: str - The type of document (e.g. "protocol", "sap", "tlf", "csr_prev")
    """
    # Verify that the study exists
    study = db.query(Study).filter(Study.id == study_id).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    # Validate file has a filename
    if not file.filename:
        raise HTTPException(status_code=400, detail="File must have a filename")
    
    # Build the storage path using the storage utility
    storage_path = build_study_source_path(study_id, file.filename)
    
    # Save the uploaded file to disk
    try:
        content = await file.read()
        with open(storage_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Create relative path for storage_path (e.g. "study_1/protocol.pdf")
    relative_storage_path = f"study_{study_id}/{file.filename}"
    
    # Get current username if available (optional - can be wired later)
    uploaded_by = None
    # TODO: When authentication is wired, uncomment the dependency parameter above
    # and uncomment below:
    # if current_user:
    #     uploaded_by = current_user.username
    
    # Create SourceDocument DB record
    source_doc = SourceDocument(
        study_id=study_id,
        type=type,
        file_name=file.filename,
        storage_path=relative_storage_path,
        uploaded_at=datetime.utcnow(),
        uploaded_by=uploaded_by,
    )
    db.add(source_doc)
    db.commit()
    db.refresh(source_doc)
    
    # Trigger RAG ingestion after document is saved
    try:
        chunks_count = ingest_source_document_to_rag(db, source_doc.id)
        logger.debug(f"RAG ingestion completed for source_document_id={source_doc.id}, created {chunks_count} chunks")
    except Exception as e:
        # Log but don't fail the upload if ingestion fails
        logger.error(f"RAG ingestion failed for source_document_id={source_doc.id}: {e}", exc_info=True)
    
    return source_doc


@router.get("/{study_id}", response_model=List[SourceDocumentRead])
def list_source_documents(
    study_id: int,
    db: Session = Depends(get_db),
):
    """
    List all source documents for a given study, ordered by uploaded_at desc.
    """
    # Verify that the study exists
    study = db.query(Study).filter(Study.id == study_id).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    # Get all source documents for the study, ordered by uploaded_at desc
    source_documents = (
        db.query(SourceDocument)
        .filter(SourceDocument.study_id == study_id)
        .order_by(SourceDocument.uploaded_at.desc())
        .all()
    )
    
    return source_documents
