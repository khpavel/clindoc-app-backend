"""
Unit tests for study members management endpoint.

Tests that:
1. Study owner can successfully add members
2. Non-owner users receive 403 Forbidden when trying to add members
3. Adding the same user twice returns 400 Bad Request
4. Adding non-existent user returns 404 Not Found
5. Attempting to change owner through this endpoint returns 400
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.study import Study
from app.models.study_member import StudyMember
from app.models.user import User
from app.core.security import create_access_token
from app.core.config import settings
from datetime import timedelta


def get_auth_headers(user: User) -> dict:
    """Helper to create auth headers for a user."""
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    return {"Authorization": f"Bearer {access_token}"}


# DELETE endpoint tests

def test_owner_can_delete_member(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study,
    other_user: User
):
    """
    Test that a study owner can successfully delete a member (editor/viewer).
    """
    # Add other_user as editor
    member = StudyMember(
        user_id=other_user.id,
        study_id=test_study.id,
        role="editor"
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    
    headers = get_auth_headers(test_user)
    
    response = client.delete(
        f"/api/v1/studies/{test_study.id}/members/{member.id}",
        headers=headers
    )
    
    assert response.status_code == 204
    
    # Verify the member was actually deleted from the database
    deleted_member = db.query(StudyMember).filter(StudyMember.id == member.id).first()
    assert deleted_member is None


def test_owner_cannot_delete_self_as_last_owner(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study
):
    """
    Test that owner cannot delete themselves if they are the only owner.
    """
    # Find the owner membership
    owner_member = (
        db.query(StudyMember)
        .filter(
            StudyMember.study_id == test_study.id,
            StudyMember.user_id == test_user.id,
            StudyMember.role == "owner"
        )
        .first()
    )
    assert owner_member is not None
    
    headers = get_auth_headers(test_user)
    
    response = client.delete(
        f"/api/v1/studies/{test_study.id}/members/{owner_member.id}",
        headers=headers
    )
    
    assert response.status_code == 400
    assert "last owner" in response.json()["detail"].lower()
    
    # Verify the member was NOT deleted
    still_exists = db.query(StudyMember).filter(StudyMember.id == owner_member.id).first()
    assert still_exists is not None


def test_owner_can_delete_self_when_other_owners_exist(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study,
    other_user: User
):
    """
    Test that owner can delete themselves if there are other owners.
    """
    # Add other_user as owner
    other_owner = StudyMember(
        user_id=other_user.id,
        study_id=test_study.id,
        role="owner"
    )
    db.add(other_owner)
    db.commit()
    db.refresh(other_owner)
    
    # Find the test_user's owner membership
    owner_member = (
        db.query(StudyMember)
        .filter(
            StudyMember.study_id == test_study.id,
            StudyMember.user_id == test_user.id,
            StudyMember.role == "owner"
        )
        .first()
    )
    assert owner_member is not None
    
    headers = get_auth_headers(test_user)
    
    response = client.delete(
        f"/api/v1/studies/{test_study.id}/members/{owner_member.id}",
        headers=headers
    )
    
    assert response.status_code == 204
    
    # Verify the member was actually deleted
    deleted_member = db.query(StudyMember).filter(StudyMember.id == owner_member.id).first()
    assert deleted_member is None


def test_non_owner_cannot_delete_member(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study,
    other_user: User
):
    """
    Test that a user without owner role (editor/viewer) receives 403 when trying to delete members.
    """
    # Add other_user as editor
    editor_member = StudyMember(
        user_id=other_user.id,
        study_id=test_study.id,
        role="editor"
    )
    db.add(editor_member)
    db.commit()
    db.refresh(editor_member)
    
    # Create a third user to try to delete
    third_user = User(
        username="thirduser",
        email="third@example.com",
        hashed_password="hashed",
        is_active=True
    )
    db.add(third_user)
    db.commit()
    db.refresh(third_user)
    
    # Add third_user as viewer
    viewer_member = StudyMember(
        user_id=third_user.id,
        study_id=test_study.id,
        role="viewer"
    )
    db.add(viewer_member)
    db.commit()
    db.refresh(viewer_member)
    
    # Try to delete viewer_member as editor (other_user)
    headers = get_auth_headers(other_user)
    
    response = client.delete(
        f"/api/v1/studies/{test_study.id}/members/{viewer_member.id}",
        headers=headers
    )
    
    assert response.status_code == 403
    assert "owner" in response.json()["detail"].lower() or "manage" in response.json()["detail"].lower()
    
    # Verify the member was NOT deleted
    still_exists = db.query(StudyMember).filter(StudyMember.id == viewer_member.id).first()
    assert still_exists is not None


def test_delete_nonexistent_member_returns_404(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study
):
    """
    Test that attempting to delete a non-existent member returns 404.
    """
    headers = get_auth_headers(test_user)
    nonexistent_member_id = 99999
    
    response = client.delete(
        f"/api/v1/studies/{test_study.id}/members/{nonexistent_member_id}",
        headers=headers
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_delete_member_from_different_study_returns_404(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study,
    other_user: User
):
    """
    Test that attempting to delete a member that belongs to a different study returns 404.
    """
    # Create another study
    other_study = Study(
        code="OTHER001",
        title="Other Study",
        owner_id=other_user.id,
        status="draft"
    )
    db.add(other_study)
    db.flush()
    
    # Add other_user as member of other_study
    other_study_member = StudyMember(
        user_id=other_user.id,
        study_id=other_study.id,
        role="owner"
    )
    db.add(other_study_member)
    db.commit()
    db.refresh(other_study_member)
    
    # Try to delete member from other_study using test_study.id
    headers = get_auth_headers(test_user)
    
    response = client.delete(
        f"/api/v1/studies/{test_study.id}/members/{other_study_member.id}",
        headers=headers
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
    
    # Verify the member was NOT deleted
    still_exists = db.query(StudyMember).filter(StudyMember.id == other_study_member.id).first()
    assert still_exists is not None


def test_unauthorized_user_cannot_delete_member(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study,
    other_user: User
):
    """
    Test that an unauthorized (non-member) user cannot delete members.
    """
    # Add a third user as member
    third_user = User(
        username="thirduser",
        email="third@example.com",
        hashed_password="hashed",
        is_active=True
    )
    db.add(third_user)
    db.commit()
    db.refresh(third_user)
    
    member = StudyMember(
        user_id=third_user.id,
        study_id=test_study.id,
        role="viewer"
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    
    # other_user is not a member of test_study
    headers = get_auth_headers(other_user)
    
    response = client.delete(
        f"/api/v1/studies/{test_study.id}/members/{member.id}",
        headers=headers
    )
    
    assert response.status_code == 403
    
    # Verify the member was NOT deleted
    still_exists = db.query(StudyMember).filter(StudyMember.id == member.id).first()
    assert still_exists is not None


# GET /api/v1/studies/{study_id}/members endpoint tests

def test_member_can_list_study_members(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study,
    other_user: User
):
    """
    Test that a study member can successfully get the list of study members.
    """
    # Add other_user as editor
    editor_member = StudyMember(
        user_id=other_user.id,
        study_id=test_study.id,
        role="editor"
    )
    db.add(editor_member)
    db.commit()
    
    headers = get_auth_headers(test_user)
    
    response = client.get(
        f"/api/v1/studies/{test_study.id}/members",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2  # test_user (owner) and other_user (editor)
    
    # Check that both members are in the list
    user_ids = [member["user_id"] for member in data]
    assert test_user.id in user_ids
    assert other_user.id in user_ids
    
    # Check that roles are correct
    for member in data:
        assert "id" in member
        assert "study_id" in member
        assert "user_id" in member
        assert "role" in member
        assert "created_at" in member
        if member["user_id"] == test_user.id:
            assert member["role"] == "owner"
        elif member["user_id"] == other_user.id:
            assert member["role"] == "editor"


def test_non_member_cannot_list_study_members(
    client: TestClient,
    db: Session,
    test_study: Study,
    other_user: User
):
    """
    Test that a non-member user receives 403 when trying to list study members.
    """
    # other_user is not a member of test_study
    headers = get_auth_headers(other_user)
    
    response = client.get(
        f"/api/v1/studies/{test_study.id}/members",
        headers=headers
    )
    
    assert response.status_code == 403
    assert "member" in response.json()["detail"].lower() or "access denied" in response.json()["detail"].lower()


def test_list_members_for_nonexistent_study_returns_404(
    client: TestClient,
    db: Session,
    test_user: User
):
    """
    Test that attempting to list members for a non-existent study returns 404.
    """
    headers = get_auth_headers(test_user)
    nonexistent_study_id = 99999
    
    response = client.get(
        f"/api/v1/studies/{nonexistent_study_id}/members",
        headers=headers
    )
    
    assert response.status_code == 404
    assert "study not found" in response.json()["detail"].lower()


# POST /api/v1/studies/{study_id}/members/{user_id} endpoint tests

def test_owner_can_add_member_by_user_id(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study,
    other_user: User
):
    """
    Test that a study owner can successfully add a member using user_id in path.
    """
    headers = get_auth_headers(test_user)
    
    response = client.post(
        f"/api/v1/studies/{test_study.id}/members/{other_user.id}",
        json={
            "role": "editor"
        },
        headers=headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == other_user.id
    assert data["study_id"] == test_study.id
    assert data["role"] == "editor"
    assert "id" in data
    assert "created_at" in data
    
    # Verify the member was actually added to the database
    member = db.query(StudyMember).filter(
        StudyMember.study_id == test_study.id,
        StudyMember.user_id == other_user.id
    ).first()
    assert member is not None
    assert member.role == "editor"


def test_non_owner_cannot_add_member_by_user_id(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study,
    other_user: User
):
    """
    Test that a user without owner role receives 403 when trying to add members via user_id path.
    """
    # Add other_user as editor (not owner)
    editor_member = StudyMember(
        user_id=other_user.id,
        study_id=test_study.id,
        role="editor"
    )
    db.add(editor_member)
    db.commit()
    
    # Create a third user to try to add
    third_user = User(
        username="thirduser",
        email="third@example.com",
        hashed_password="hashed",
        is_active=True
    )
    db.add(third_user)
    db.commit()
    db.refresh(third_user)
    
    headers = get_auth_headers(other_user)
    
    response = client.post(
        f"/api/v1/studies/{test_study.id}/members/{third_user.id}",
        json={
            "role": "viewer"
        },
        headers=headers
    )
    
    assert response.status_code == 403
    assert "owner" in response.json()["detail"].lower() or "access denied" in response.json()["detail"].lower()


def test_cannot_add_duplicate_member_by_user_id(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study,
    other_user: User
):
    """
    Test that adding the same user twice via user_id path returns 400 Bad Request.
    """
    # First, add the user as a member
    member = StudyMember(
        user_id=other_user.id,
        study_id=test_study.id,
        role="viewer"
    )
    db.add(member)
    db.commit()
    
    headers = get_auth_headers(test_user)
    
    # Try to add the same user again
    response = client.post(
        f"/api/v1/studies/{test_study.id}/members/{other_user.id}",
        json={
            "role": "editor"
        },
        headers=headers
    )
    
    assert response.status_code == 400
    assert "already in study" in response.json()["detail"].lower()


def test_cannot_add_nonexistent_user_by_user_id(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study
):
    """
    Test that adding a non-existent user via user_id path returns 404 Not Found.
    """
    headers = get_auth_headers(test_user)
    nonexistent_user_id = 99999
    
    response = client.post(
        f"/api/v1/studies/{test_study.id}/members/{nonexistent_user_id}",
        json={
            "role": "viewer"
        },
        headers=headers
    )
    
    assert response.status_code == 404
    assert "user not found" in response.json()["detail"].lower()


def test_cannot_add_owner_role_by_user_id_when_owner_exists(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study,
    other_user: User
):
    """
    Test that attempting to add a new owner via user_id path when one already exists returns 400.
    """
    headers = get_auth_headers(test_user)
    
    # Try to add other_user as owner (test_user is already owner)
    response = client.post(
        f"/api/v1/studies/{test_study.id}/members/{other_user.id}",
        json={
            "role": "owner"
        },
        headers=headers
    )
    
    assert response.status_code == 400
    assert "owner" in response.json()["detail"].lower()


def test_unauthorized_user_cannot_add_member_by_user_id(
    client: TestClient,
    db: Session,
    test_study: Study,
    other_user: User
):
    """
    Test that an unauthorized (non-member) user cannot add members via user_id path.
    """
    # other_user is not a member of test_study
    headers = get_auth_headers(other_user)
    
    # Create a third user to try to add
    third_user = User(
        username="thirduser",
        email="third@example.com",
        hashed_password="hashed",
        is_active=True
    )
    db.add(third_user)
    db.commit()
    db.refresh(third_user)
    
    response = client.post(
        f"/api/v1/studies/{test_study.id}/members/{third_user.id}",
        json={
            "role": "viewer"
        },
        headers=headers
    )
    
    assert response.status_code == 403