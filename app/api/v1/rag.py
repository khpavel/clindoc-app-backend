import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.source import SourceDocument
from app.services.rag_ingest import ingest_source_document_to_rag

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/ingest/{source_document_id}")
def ingest_source_document(
    source_document_id: int,
    db: Session = Depends(get_db),
):
    """
    Trigger RAG ingestion for a source document.
    
    - Reads the source document file
    - Extracts text and chunks it
    - Creates RagChunk records in the database
    - Returns the number of chunks created
    """
    # Verify that the source document exists
    source_doc = db.query(SourceDocument).filter(SourceDocument.id == source_document_id).first()
    if not source_doc:
        raise HTTPException(status_code=404, detail="Source document not found")
    
    try:
        chunks_count = ingest_source_document_to_rag(db, source_document_id)
        logger.info(f"RAG ingestion completed for source_document_id={source_document_id}, created {chunks_count} chunks")
        return {"source_document_id": source_document_id, "chunks_created": chunks_count}
    except Exception as e:
        logger.error(f"RAG ingestion failed for source_document_id={source_document_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"RAG ingestion failed: {str(e)}")

