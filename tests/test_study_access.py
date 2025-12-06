"""
Unit tests for study access control.

Tests that:
1. Study members can access studies they belong to
2. Non-members receive 403 Forbidden when trying to access studies
"""
import pytest
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.study import Study
from app.models.study_member import StudyMember
from app.models.user import User
from app.deps.study_access import verify_study_access


def test_study_member_can_access_study(db: Session, test_user: User, test_study: Study):
    """
    Test that a user who is a member of a study can access it.
    """
    # Create a StudyMember record
    study_member = StudyMember(
        user_id=test_user.id,
        study_id=test_study.id,
        role="viewer"
    )
    db.add(study_member)
    db.commit()
    
    # Verify access - should not raise an exception
    result = verify_study_access(test_study.id, test_user.id, db)
    
    assert result is not None
    assert result.id == test_study.id
    assert isinstance(result, Study)


def test_non_member_cannot_access_study(db: Session, test_user: User, test_study: Study, other_user: User):
    """
    Test that a user who is NOT a member of a study receives 403 Forbidden.
    """
    # Create a StudyMember for a different user
    study_member = StudyMember(
        user_id=other_user.id,
        study_id=test_study.id,
        role="owner"
    )
    db.add(study_member)
    db.commit()
    
    # Try to access the study as test_user (who is not a member)
    with pytest.raises(HTTPException) as exc_info:
        verify_study_access(test_study.id, test_user.id, db)
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "not a member" in exc_info.value.detail.lower()


def test_nonexistent_study_returns_404(db: Session, test_user: User):
    """
    Test that accessing a non-existent study returns 404 Not Found.
    """
    nonexistent_study_id = 99999
    
    with pytest.raises(HTTPException) as exc_info:
        verify_study_access(nonexistent_study_id, test_user.id, db)
    
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in exc_info.value.detail.lower()


def test_study_owner_can_access_study(db: Session, test_user: User, test_study: Study):
    """
    Test that a user with owner role can access the study.
    """
    # Create a StudyMember with owner role
    study_member = StudyMember(
        user_id=test_user.id,
        study_id=test_study.id,
        role="owner"
    )
    db.add(study_member)
    db.commit()
    
    # Verify access
    result = verify_study_access(test_study.id, test_user.id, db)
    assert result.id == test_study.id


def test_study_editor_can_access_study(db: Session, test_user: User, test_study: Study):
    """
    Test that a user with editor role can access the study.
    """
    # Create a StudyMember with editor role
    study_member = StudyMember(
        user_id=test_user.id,
        study_id=test_study.id,
        role="editor"
    )
    db.add(study_member)
    db.commit()
    
    # Verify access
    result = verify_study_access(test_study.id, test_user.id, db)
    assert result.id == test_study.id

