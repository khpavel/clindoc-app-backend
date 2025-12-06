"""
Service functions for study members management.
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.models.study_member import StudyMember


def get_user_study_role(db: Session, user_id: int, study_id: int) -> Optional[str]:
    """
    Получить роль пользователя в исследовании.
    
    Args:
        db: Database session
        user_id: ID пользователя
        study_id: ID исследования
        
    Returns:
        Роль пользователя ("owner", "editor", "viewer") или None, если пользователь не является участником
    """
    membership = (
        db.query(StudyMember)
        .filter(
            StudyMember.study_id == study_id,
            StudyMember.user_id == user_id
        )
        .first()
    )
    
    if not membership:
        return None
    
    return membership.role

