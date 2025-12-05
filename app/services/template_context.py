from typing import Any

from sqlalchemy.orm import Session

from app.models.study import Study


def build_template_context(
    db: Session,
    study_id: int,
    extra_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Load the Study and build a base context dict for template rendering.
    Extra context keys override or extend the base context.
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

    if extra_context:
        ctx.update(extra_context)

    return ctx

