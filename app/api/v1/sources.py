import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.storage import build_study_source_path, delete_file
from app.db.session import get_db, SessionLocal
from app.deps.auth import get_current_active_user
from app.deps.study_access import get_study_for_user_or_403, verify_study_editor_access, verify_study_management_access
from app.deps.language import get_request_language
from app.models.source import SourceDocument
from app.models.rag import RagChunk
from app.models.study import Study
from app.models.user import User
from app.schemas.source import SourceDocumentRead
from app.services.rag_ingest import ingest_source_document_to_rag

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sources", tags=["sources"])


def _run_ingestion_background(source_document_id: int) -> None:
    """
    Background task to run RAG ingestion for a source document.
    Sets index_status to 'indexed' on success or 'error' on failure.
    Creates a new database session for the background task.
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting RAG ingestion for source_document_id={source_document_id}")
        chunks_count = ingest_source_document_to_rag(db, source_document_id)
        logger.info(f"RAG ingestion completed successfully for source_document_id={source_document_id}, created {chunks_count} chunks")
    except Exception as e:
        # Error is already logged and index_status set to 'error' inside ingest_source_document_to_rag
        logger.error(f"RAG ingestion failed for source_document_id={source_document_id}: {e}", exc_info=True)
    finally:
        db.close()


@router.post("/{study_id}/upload", response_model=SourceDocumentRead)
async def upload_source_document(
    study_id: int,
    file: UploadFile = File(...),
    type: str = Form(...),
    language: str = Form("ru"),
    version_label: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    study: Study = Depends(get_study_for_user_or_403),
):
    """
    Upload a source document for a study.
    
    - Accepts multipart/form-data with:
      - file: UploadFile - The document file to upload
      - type: str - The type of document (e.g. "protocol", "sap", "tlf", "csr_prev")
      - language: str - Language code ("ru" or "en"), default "ru"
      - version_label: str (optional) - Version label for the document
    """
    
    # Validate file has a filename
    if not file.filename:
        raise HTTPException(status_code=400, detail="File must have a filename")
    
    # Validate language
    if language not in ("ru", "en"):
        raise HTTPException(status_code=400, detail="Language must be 'ru' or 'en'")
    
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
    
    # Mark all previous documents with the same (study_id, type, language) as not current
    db.query(SourceDocument).filter(
        SourceDocument.study_id == study_id,
        SourceDocument.type == type,
        SourceDocument.language == language,
        SourceDocument.is_current == True
    ).update({"is_current": False})
    
    # Create SourceDocument DB record
    # Set index_status to "not_indexed" before ingestion starts
    source_doc = SourceDocument(
        study_id=study_id,
        type=type,
        file_name=file.filename,
        storage_path=relative_storage_path,
        uploaded_at=datetime.utcnow(),
        uploaded_by=uploaded_by,
        language=language,
        version_label=version_label,
        status="active",
        is_current=True,
        is_rag_enabled=True,
        index_status="not_indexed",
    )
    db.add(source_doc)
    db.commit()
    db.refresh(source_doc)
    
    # Trigger automatic RAG ingestion after document is saved (only if is_rag_enabled is True)
    # Ingestion runs in background task to avoid blocking the response
    # Status will be updated to "indexed" on success or "error" on failure
    if source_doc.is_rag_enabled:
        background_tasks.add_task(_run_ingestion_background, source_doc.id)
        logger.info(f"Scheduled RAG ingestion for source_document_id={source_doc.id}, file={file.filename}")
    
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


def _cleanup_rag_chunks_for_document(db: Session, source_document_id: int) -> None:
    """
    Helper function to delete all RagChunk records associated with a source document.
    
    Args:
        db: Database session
        source_document_id: ID of the source document
    """
    deleted_count = (
        db.query(RagChunk)
        .filter(RagChunk.source_document_id == source_document_id)
        .delete()
    )
    logger.info(f"Deleted {deleted_count} RAG chunks for source_document_id={source_document_id}")


def _determine_is_current_on_restore(
    db: Session,
    study_id: int,
    doc_type: str,
    language: str,
    restored_doc_id: int
) -> bool:
    """
    Helper function to determine if a restored document should be marked as is_current.
    
    Logic:
    - Default: set is_current = False to avoid silently changing which version is "current"
    - If there are no other active documents of the same (study_id, type, language),
      set is_current = True
    
    Args:
        db: Database session
        study_id: ID of the study
        doc_type: Type of the document
        language: Language of the document
        restored_doc_id: ID of the document being restored (to exclude from check)
    
    Returns:
        bool: True if the document should be marked as current, False otherwise
    """
    # Check if there are any other active documents with the same (study_id, type, language)
    other_active_docs = (
        db.query(SourceDocument)
        .filter(
            SourceDocument.study_id == study_id,
            SourceDocument.type == doc_type,
            SourceDocument.language == language,
            SourceDocument.id != restored_doc_id,
            SourceDocument.status == "active"
        )
        .count()
    )
    
    # If no other active documents exist, mark this one as current
    return other_active_docs == 0


@router.delete("/{source_document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source_document(
    source_document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    language: str = Depends(get_request_language),
):
    """
    Soft delete a source document.
    
    - Sets status="archived", is_current=False, is_rag_enabled=False
    - Deletes associated RAG chunks
    - Only owners and editors can delete documents (viewers are not allowed)
    - Returns 204 No Content on success
    """
    
    # Load the source document
    source_doc = db.query(SourceDocument).filter(SourceDocument.id == source_document_id).first()
    if not source_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source document not found"
        )
    
    # Verify user has editor access (owner or editor role) to the study
    verify_study_editor_access(source_doc.study_id, current_user.id, db, language=language)
    
    # Soft delete: update status and flags
    source_doc.status = "archived"
    source_doc.is_current = False
    source_doc.is_rag_enabled = False
    # Optionally reset index_status
    source_doc.index_status = "not_indexed"
    
    # Clean up RAG chunks for this document
    _cleanup_rag_chunks_for_document(db, source_document_id)
    
    # Commit the transaction
    db.commit()
    
    logger.info(f"Soft deleted source_document_id={source_document_id} by user_id={current_user.id}")
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{source_document_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
def permanent_delete_source_document(
    source_document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    language: str = Depends(get_request_language),
):
    """
    Permanently delete a source document, its RAG chunks and stored file.
    
    This action is irreversible. Only study owners can perform permanent delete.
    
    - Deletes all associated RAG chunks
    - Physically deletes the file from storage
    - Removes the SourceDocument record from the database
    
    Returns 204 No Content on success.
    """
    
    # Load the source document
    source_doc = db.query(SourceDocument).filter(SourceDocument.id == source_document_id).first()
    if not source_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source document not found"
        )
    
    # Verify user has owner access (only owners can permanently delete)
    verify_study_management_access(source_doc.study_id, current_user.id, db, language=language)
    
    # Store values before deletion for cleanup and logging
    storage_path_to_delete = source_doc.storage_path
    study_id = source_doc.study_id
    
    # Clean up RAG chunks for this document
    _cleanup_rag_chunks_for_document(db, source_document_id)
    
    # Delete the document from database
    db.delete(source_doc)
    db.commit()
    
    # Delete the physical file from storage
    # If file deletion fails, log error but don't fail the operation
    # (the DB record is already deleted at this point)
    file_deleted = delete_file(storage_path_to_delete)
    if not file_deleted:
        logger.warning(
            f"Failed to delete physical file for source_document_id={source_document_id}, "
            f"storage_path={storage_path_to_delete}. Database record was already deleted."
        )
    
    logger.info(
        f"Permanently deleted source_document_id={source_document_id} "
        f"by user_id={current_user.id} (study_id={study_id})"
    )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{source_document_id}/restore", response_model=SourceDocumentRead)
def restore_source_document(
    source_document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    language: str = Depends(get_request_language),
):
    """
    Restore a previously archived source document back to active state.
    
    - Sets status="active", is_rag_enabled=True, index_status="not_indexed"
    - Determines is_current based on whether other active documents exist
    - Triggers RAG ingestion to re-index the document
    - Only owners and editors can restore documents (viewers are not allowed)
    - Returns the restored document
    """
    
    # Load the source document
    source_doc = db.query(SourceDocument).filter(SourceDocument.id == source_document_id).first()
    if not source_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source document not found"
        )
    
    # Check if document is archived
    if source_doc.status != "archived":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document is not archived"
        )
    
    # Verify user has editor access (owner or editor role) to the study
    verify_study_editor_access(source_doc.study_id, current_user.id, db, language=language)
    
    # Determine is_current value using helper function
    should_be_current = _determine_is_current_on_restore(
        db, source_doc.study_id, source_doc.type, source_doc.language, source_doc.id
    )
    
    # Restore state: set status, is_rag_enabled, index_status, and is_current
    source_doc.status = "active"
    source_doc.is_rag_enabled = True
    source_doc.index_status = "not_indexed"
    source_doc.is_current = should_be_current
    
    # Commit the transaction first
    db.commit()
    db.refresh(source_doc)
    
    # Trigger RAG ingestion after document is restored (only if is_rag_enabled is True)
    if source_doc.is_rag_enabled:
        try:
            logger.info(f"Starting RAG ingestion for restored source_document_id={source_doc.id}, file={source_doc.file_name}")
            chunks_count = ingest_source_document_to_rag(db, source_doc.id)
            logger.info(f"RAG ingestion completed successfully for restored source_document_id={source_doc.id}, created {chunks_count} chunks")
        except Exception as e:
            # Log but don't fail the restore if ingestion fails
            logger.error(f"RAG ingestion failed for restored source_document_id={source_doc.id}, file={source_doc.file_name}: {e}", exc_info=True)
    
    logger.info(f"Restored source_document_id={source_document_id} by user_id={current_user.id}")
    
    return source_doc
