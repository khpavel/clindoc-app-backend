from typing import Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, or_

from app.models.rag import RagChunk
from app.models.source import SourceDocument


def retrieve_rag_chunks(
    db: Session,
    study_id: int,
    source_types: list[str] | None = None,
    limit_per_source: int = 5,
    content_language: Optional[str] = None,
) -> dict[str, list[RagChunk]]:
    """
    Retrieve a small set of chunks per source_type for a study.
    
    When content_language is provided, prefers chunks from SourceDocuments
    matching that language. If no matching chunks are found, falls back to
    all chunks regardless of language.
    
    Args:
        db: Database session
        study_id: ID of the study
        source_types: Optional list of source types to filter by. Defaults to all.
        limit_per_source: Maximum number of chunks to retrieve per source type
        content_language: Optional language code ("ru" or "en") to prefer chunks
                         from SourceDocuments matching this language
    
    Returns:
        Dictionary mapping source_type to list of RagChunk objects
    """
    if source_types is None:
        source_types = ["protocol", "sap", "tlf", "csr_prev"]
    
    result: dict[str, list[RagChunk]] = {}
    
    for stype in source_types:
        chunks = []
        
        if content_language and content_language in ("ru", "en"):
            # First, try to get chunks from source documents matching content_language
            # Only include chunks that have a source_document with matching language
            stmt = (
                select(RagChunk)
                .join(SourceDocument, RagChunk.source_document_id == SourceDocument.id)
                .where(RagChunk.study_id == study_id)
                .where(RagChunk.source_type == stype)
                .where(SourceDocument.language == content_language)
                .order_by(RagChunk.order_index)
                .limit(limit_per_source)
            )
            matching_chunks = list(db.execute(stmt).scalars().all())
            
            if matching_chunks:
                chunks = matching_chunks
            else:
                # If no matching language chunks found, fall back to all chunks
                # This allows using documents in other languages as a fallback
                stmt = (
                    select(RagChunk)
                    .where(RagChunk.study_id == study_id)
                    .where(RagChunk.source_type == stype)
                    .order_by(RagChunk.order_index)
                    .limit(limit_per_source)
                )
                chunks = list(db.execute(stmt).scalars().all())
        else:
            # No content_language specified, get all chunks
            stmt = (
                select(RagChunk)
                .where(RagChunk.study_id == study_id)
                .where(RagChunk.source_type == stype)
                .order_by(RagChunk.order_index)
                .limit(limit_per_source)
            )
            chunks = list(db.execute(stmt).scalars().all())
        
        result[stype] = chunks
    
    return result


def build_rag_context_text(chunks_by_type: dict[str, list[RagChunk]]) -> dict[str, str]:
    """
    Build concatenated context blocks for each source_type, e.g.:
    { "protocol": "...", "sap": "...", ... }.
    """
    result: dict[str, str] = {}
    
    for source_type, chunks in chunks_by_type.items():
        texts = [chunk.text for chunk in chunks]
        result[source_type] = "\n\n".join(texts)
    
    return result

