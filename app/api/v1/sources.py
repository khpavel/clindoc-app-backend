import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.storage import build_study_source_path
from app.db.session import get_db
from app.deps.auth import get_current_active_user
from app.deps.study_access import get_study_for_user_or_403
from app.models.source import SourceDocument
from app.models.study import Study
from app.models.user import User
from app.schemas.source import SourceDocumentRead
from app.services.rag_ingest import ingest_source_document_to_rag

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sources", tags=["sources"])


@router.post("/{study_id}/upload", response_model=SourceDocumentRead)
async def upload_source_document(
    study_id: int,
    file: UploadFile = File(...),
    type: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    study: Study = Depends(get_study_for_user_or_403),
):
    """
    Upload a source document for a study.
    
    - Accepts multipart/form-data with:
      - file: UploadFile - The document file to upload
      - type: str - The type of document (e.g. "protocol", "sap", "tlf", "csr_prev")
    """
    
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
    
    # Get current username
    uploaded_by = current_user.username
    
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
    
    # Trigger automatic RAG ingestion after document is saved
    try:
        logger.info(f"Starting automatic RAG ingestion for source_document_id={source_doc.id}, file={file.filename}")
        chunks_count = ingest_source_document_to_rag(db, source_doc.id)
        logger.info(f"RAG ingestion completed successfully for source_document_id={source_doc.id}, created {chunks_count} chunks")
    except Exception as e:
        # Log but don't fail the upload if ingestion fails
        logger.error(f"RAG ingestion failed for source_document_id={source_doc.id}, file={file.filename}: {e}", exc_info=True)
    
    return source_doc


@router.get("/{study_id}", response_model=List[SourceDocumentRead])
def list_source_documents(
    study_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    study: Study = Depends(get_study_for_user_or_403),
):
    """
    List all source documents for a given study, ordered by uploaded_at desc.
    """
    
    # Get all source documents for the study, ordered by uploaded_at desc
    source_documents = (
        db.query(SourceDocument)
        .filter(SourceDocument.study_id == study_id)
        .order_by(SourceDocument.uploaded_at.desc())
        .all()
    )
    
    return source_documents
