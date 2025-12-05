from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.rag import RagChunk


def retrieve_rag_chunks(
    db: Session,
    study_id: int,
    source_types: list[str] | None = None,
    limit_per_source: int = 5,
) -> dict[str, list[RagChunk]]:
    """
    Retrieve a small set of chunks per source_type for a study.
    For MVP, just select the earliest chunks (by order_index).
    Returns a dict {source_type: [RagChunk, ...]}.
    """
    if source_types is None:
        source_types = ["protocol", "sap", "tlf", "csr_prev"]
    
    result: dict[str, list[RagChunk]] = {}
    
    for stype in source_types:
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

