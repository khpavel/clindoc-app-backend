from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps.auth import get_current_active_user
from app.models.study import Study
from app.models.study_member import StudyMember
from app.models.user import User


def verify_study_access(study_id: int, user_id: int, db: Session) -> Study:
    """
    Helper function to verify user access to a study.
    Returns the Study if access is granted, raises HTTPException if not.
    """
    # First check if study exists
    study = db.query(Study).filter(Study.id == study_id).first()
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check if user is a member of the study
    membership = (
        db.query(StudyMember)
        .filter(
            StudyMember.study_id == study_id,
            StudyMember.user_id == user_id
        )
        .first()
    )
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not a member of this study"
        )
    
    return study


def get_study_for_user_or_403(
    study_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Study:
    """
    Dependency that verifies the current user has access to the study.
    
    Checks if there's a StudyMember record for the user and study.
    Returns the Study if access is granted, raises 403 if not.
    Also raises 404 if the study doesn't exist.
    
    Use this as a dependency for endpoints where study_id is a path parameter.
    """
    return verify_study_access(study_id, current_user.id, db)


def verify_study_management_access(study_id: int, user_id: int, db: Session) -> Study:
    """
    Helper function to verify user has management access to a study (owner or admin).
    Returns the Study if access is granted, raises HTTPException if not.
    
    Currently only checks for owner role. Can be extended to check for global admin role.
    """
    # First check if study exists
    study = db.query(Study).filter(Study.id == study_id).first()
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check if user is an owner of the study
    membership = (
        db.query(StudyMember)
        .filter(
            StudyMember.study_id == study_id,
            StudyMember.user_id == user_id,
            StudyMember.role == "owner"
        )
        .first()
    )
    
    if not membership:
        # TODO: Add check for global admin role when implemented
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Only study owners can manage members"
        )
    
    return study


def get_study_for_management_or_403(
    study_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Study:
    """
    Dependency that verifies the current user has management access to the study.
    
    Checks if the user is an owner (or admin in the future).
    Returns the Study if access is granted, raises 403 if not.
    Also raises 404 if the study doesn't exist.
    
    Use this as a dependency for endpoints that require managing study members.
    """
    return verify_study_management_access(study_id, current_user.id, db)


def verify_study_editor_access(study_id: int, user_id: int, db: Session) -> Study:
    """
    Helper function to verify user has editor access to a study (owner or editor).
    Returns the Study if access is granted, raises HTTPException if not.
    
    This is used for operations that require owner or editor role (e.g., uploading/deleting source documents).
    """
    # First check if study exists
    study = db.query(Study).filter(Study.id == study_id).first()
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
    # Check if user is a member of the study
    membership = (
        db.query(StudyMember)
        .filter(
            StudyMember.study_id == study_id,
            StudyMember.user_id == user_id
        )
        .first()
    )
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not a member of this study"
        )
    
    # Check if user has owner or editor role (viewer is not allowed)
    if membership.role not in ("owner", "editor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Only study owners and editors can perform this action"
        )
    
    return study


def get_study_for_editor_or_403(
    study_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Study:
    """
    Dependency that verifies the current user has editor access to the study (owner or editor).
    
    Checks if the user is an owner or editor (viewer is not allowed).
    Returns the Study if access is granted, raises 403 if not.
    Also raises 404 if the study doesn't exist.
    
    Use this as a dependency for endpoints that require owner/editor role (e.g., source document operations).
    """
    return verify_study_editor_access(study_id, current_user.id, db)