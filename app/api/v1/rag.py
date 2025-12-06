import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func

from app.db.session import get_db
from app.deps.auth import get_current_active_user
from app.deps.study_access import get_study_for_user_or_403
from app.models.rag import RagChunk
from app.models.study import Study
from app.models.source import SourceDocument
from app.models.user import User
from app.schemas.rag import RagChunkRead, RagStudyChunksResponse
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


@router.get("/{study_id}", response_model=RagStudyChunksResponse)
def get_study_rag_chunks(
    study_id: int,
    source_type: str | None = Query(default=None, description="protocol / sap / tlf / csr_prev"),
    q: str | None = Query(default=None, description="Simple substring search in chunk text"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    study: Study = Depends(get_study_for_user_or_403),
):
    """
    Diagnostic endpoint to inspect RAG chunks for a given study.
    
    Returns paginated list of chunks with optional filtering by source_type.
    """
    
    # Build a base query on RagChunk filtered by study_id
    # Use joinedload to eagerly load source_document relationship
    base_query = db.query(RagChunk).options(joinedload(RagChunk.source_document)).filter(RagChunk.study_id == study_id)
    
    # If source_type is provided, filter by RagChunk.source_type == source_type
    if source_type is not None:
        base_query = base_query.filter(RagChunk.source_type == source_type)
    
    # If q is provided, apply text filter
    if q is not None:
        base_query = base_query.filter(RagChunk.text.ilike(f"%{q}%"))
    
    # Compute total_chunks using select(func.count()) 
    count_query = select(func.count(RagChunk.id)).filter(RagChunk.study_id == study_id)
    if source_type is not None:
        count_query = count_query.filter(RagChunk.source_type == source_type)
    if q is not None:
        count_query = count_query.filter(RagChunk.text.ilike(f"%{q}%"))
    total_chunks = db.scalar(count_query) or 0
    
    # Apply order_by(RagChunk.source_type, RagChunk.order_index) and limit/offset to get page of chunks
    chunks = (
        base_query
        .order_by(RagChunk.source_type, RagChunk.order_index)
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    # Convert SQLAlchemy RagChunk instances to RagChunkRead Pydantic models
    # with truncated text preview and source document file name
    chunk_reads = []
    for chunk in chunks:
        # Truncate text to 200 characters for preview
        text_preview = chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text
        
        # Get source document file name from the eagerly loaded relationship
        source_document_file_name = chunk.source_document.file_name if chunk.source_document else None
        
        chunk_dict = {
            "id": chunk.id,
            "study_id": chunk.study_id,
            "source_document_id": chunk.source_document_id,
            "source_type": chunk.source_type,
            "order_index": chunk.order_index,
            "text": chunk.text,
            "text_preview": text_preview,
            "created_at": chunk.created_at,
            "source_document_file_name": source_document_file_name,
        }
        chunk_reads.append(RagChunkRead.model_validate(chunk_dict))
    
    # Return RagStudyChunksResponse with study_id, source_type, total_chunks, limit, offset, chunks
    return RagStudyChunksResponse(
        study_id=study_id,
        source_type=source_type,
        total_chunks=total_chunks,
        limit=limit,
        offset=offset,
        chunks=chunk_reads
    )

