from typing import Any

from sqlalchemy.orm import Session

from app.models.study import Study
from app.services.rag_retrieval import retrieve_rag_chunks, build_rag_context_text


def build_template_context(
    db: Session,
    study_id: int,
    extra_context: dict[str, Any] | None = None,
    language: str = "ru",
) -> dict[str, Any]:
    """
    Load the Study and build a base context dict for template rendering.
    Extra context keys override or extend the base context.
    
    Args:
        db: Database session
        study_id: ID of the study
        extra_context: Optional additional context variables
        language: Language code ("ru" or "en") - accepted for future language-specific context logic
    
    Returns:
        Dictionary of context variables for template rendering
    """
    study = db.query(Study).filter(Study.id == study_id).first()
    if not study:
        raise ValueError(f"Study with id {study_id} not found")

    ctx = {
        "study_id": study.id,
        "study_code": study.code,
        "study_title": study.title,
        "phase": study.phase,
        "indication": getattr(study, "indication", None),
        "sponsor_name": getattr(study, "sponsor_name", None),
    }

    # Add RAG context to template context
    ctx = add_rag_context_to_template_context(db, study_id, ctx)

    if extra_context:
        ctx.update(extra_context)

    return ctx


def add_rag_context_to_template_context(
    db: Session,
    study_id: int,
    ctx: dict[str, object],
) -> dict[str, object]:
    """
    Retrieve RAG chunks and add them to the template context under keys
    like 'context_protocol', 'context_sap', 'context_tlf_summary', 'context_csr_prev'.
    """
    # Retrieve RAG chunks and build context text
    chunks_by_type = retrieve_rag_chunks(db, study_id)
    rag_context = build_rag_context_text(chunks_by_type)
    
    # Map source types to descriptive context keys
    key_mapping = {
        "protocol": "context_protocol",
        "sap": "context_sap",
        "tlf": "context_tlf_summary",
        "csr_prev": "context_csr_prev",
    }
    
    # Add mapped RAG context to the template context
    for source_type, context_key in key_mapping.items():
        ctx[context_key] = rag_context.get(source_type, "")
    
    return ctx

