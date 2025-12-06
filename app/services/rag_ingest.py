from pathlib import Path
from sqlalchemy.orm import Session

from app.core.storage import get_storage_dir
from app.models.source import SourceDocument
from app.models.rag import RagChunk
from app.services.text_extraction import extract_text_from_file
from app.services.rag_chunking import chunk_text


def ingest_source_document_to_rag(
    db: Session,
    source_document_id: int,
) -> int:
    """
    Read the source document, chunk its text, and create RagChunk rows.
    Returns the number of chunks created.
    Updates index_status to 'indexed' on success or 'error' on failure.
    """
    # Load SourceDocument by id
    source = db.query(SourceDocument).filter(SourceDocument.id == source_document_id).first()
    if not source:
        raise ValueError(f"SourceDocument with id {source_document_id} not found")
    
    try:
        # Resolve file path using storage_path and the storage directory helper
        storage_base = get_storage_dir()
        file_path = storage_base / source.storage_path
        
        # Extract text via extract_text_from_file
        text = extract_text_from_file(file_path)
        
        # Chunk text via chunk_text
        chunks = chunk_text(text)
        
        # Before inserting, optionally delete existing RagChunk rows for this source_document_id
        db.query(RagChunk).filter(RagChunk.source_document_id == source_document_id).delete()
        
        # For each chunk, create RagChunk
        rag_chunks = []
        for order_index, chunk in enumerate(chunks):
            rag_chunk = RagChunk(
                study_id=source.study_id,
                source_document_id=source.id,
                source_type=source.type,
                order_index=order_index,
                text=chunk,
            )
            rag_chunks.append(rag_chunk)
        
        # Add all chunks to the session
        db.add_all(rag_chunks)
        
        # Update index_status to 'indexed' on success
        source.index_status = "indexed"
        db.commit()
        return len(rag_chunks)
    except Exception as e:
        # Update index_status to 'error' on failure
        source.index_status = "error"
        db.commit()
        raise e

