"""
API-level tests for user language preference.

Tests that:
1. GET /users/me returns ui_language field
2. PATCH /users/me allows updating ui_language
3. Updated ui_language persists and is returned on subsequent GET requests
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

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


def test_get_users_me_returns_ui_language(client: TestClient, db: Session, test_user: User):
    """Test that GET /users/me returns the ui_language field."""
    # Set user's ui_language to "ru"
    test_user.ui_language = "ru"
    db.commit()
    
    headers = get_auth_headers(test_user)
    
    # Get user profile
    response = client.get(
        "/api/v1/users/me",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "ui_language" in data
    assert data["ui_language"] == "ru"


def test_get_users_me_returns_default_ui_language(client: TestClient, db: Session, test_user: User):
    """Test that GET /users/me returns default ui_language if not set."""
    # Ensure ui_language is None or "en"
    test_user.ui_language = None
    db.commit()
    
    headers = get_auth_headers(test_user)
    
    # Get user profile
    response = client.get(
        "/api/v1/users/me",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "ui_language" in data
    # Should be None or default value (implementation dependent)
    assert data["ui_language"] is None or data["ui_language"] in ("en", "ru")


def test_patch_users_me_updates_ui_language(client: TestClient, db: Session, test_user: User):
    """Test that PATCH /users/me allows updating ui_language."""
    # Set initial language (if any)
    test_user.ui_language = "en"
    db.commit()
    
    headers = get_auth_headers(test_user)
    
    # Update ui_language to "ru"
    response = client.patch(
        "/api/v1/users/me",
        headers=headers,
        json={"ui_language": "ru"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["ui_language"] == "ru"
    
    # Verify it's persisted in database
    db.refresh(test_user)
    assert test_user.ui_language == "ru"


def test_patch_users_me_updates_ui_language_persists(client: TestClient, db: Session, test_user: User):
    """Test that updated ui_language persists and is returned on subsequent GET."""
    headers = get_auth_headers(test_user)
    
    # Step 1: Update ui_language to "ru"
    response1 = client.patch(
        "/api/v1/users/me",
        headers=headers,
        json={"ui_language": "ru"}
    )
    
    assert response1.status_code == 200
    assert response1.json()["ui_language"] == "ru"
    
    # Step 2: Get user profile again
    response2 = client.get(
        "/api/v1/users/me",
        headers=headers
    )
    
    assert response2.status_code == 200
    data = response2.json()
    assert data["ui_language"] == "ru"
    
    # Step 3: Update to "en"
    response3 = client.patch(
        "/api/v1/users/me",
        headers=headers,
        json={"ui_language": "en"}
    )
    
    assert response3.status_code == 200
    assert response3.json()["ui_language"] == "en"
    
    # Step 4: Get user profile again to verify
    response4 = client.get(
        "/api/v1/users/me",
        headers=headers
    )
    
    assert response4.status_code == 200
    data = response4.json()
    assert data["ui_language"] == "en"


def test_patch_users_me_rejects_invalid_ui_language(client: TestClient, db: Session, test_user: User):
    """Test that PATCH /users/me rejects invalid ui_language values."""
    headers = get_auth_headers(test_user)
    
    # Try to set invalid ui_language
    response = client.patch(
        "/api/v1/users/me",
        headers=headers,
        json={"ui_language": "fr"}  # Invalid, should be "ru" or "en"
    )
    
    # Pydantic validation should return 422
    assert response.status_code == 422
    response_data = response.json()
    # Should have validation error details
    assert "detail" in response_data


def test_patch_users_me_allows_ru_and_en(client: TestClient, db: Session, test_user: User):
    """Test that PATCH /users/me allows both "ru" and "en" values."""
    headers = get_auth_headers(test_user)
    
    # Test setting to "ru"
    response1 = client.patch(
        "/api/v1/users/me",
        headers=headers,
        json={"ui_language": "ru"}
    )
    assert response1.status_code == 200
    assert response1.json()["ui_language"] == "ru"
    
    # Test setting to "en"
    response2 = client.patch(
        "/api/v1/users/me",
        headers=headers,
        json={"ui_language": "en"}
    )
    assert response2.status_code == 200
    assert response2.json()["ui_language"] == "en"


def test_patch_users_me_partial_update(client: TestClient, db: Session, test_user: User):
    """Test that PATCH /users/me allows updating only ui_language without affecting other fields."""
    # Set initial values
    test_user.ui_language = "en"
    test_user.full_name = "Original Name"
    db.commit()
    
    headers = get_auth_headers(test_user)
    
    # Update only ui_language
    response = client.patch(
        "/api/v1/users/me",
        headers=headers,
        json={"ui_language": "ru"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["ui_language"] == "ru"
    # Other fields should remain unchanged
    assert data["full_name"] == "Original Name"
    
    # Verify in database
    db.refresh(test_user)
    assert test_user.ui_language == "ru"
    assert test_user.full_name == "Original Name"

