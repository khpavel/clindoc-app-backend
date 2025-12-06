"""
Unit tests for OutputDocument endpoints.

Tests that:
1. Study members can get output documents
2. Study members can get output document sections
3. Study members can get latest section versions
4. Study members can create section versions
5. Study members can export output documents to DOCX
6. Non-members cannot access output documents (403)
7. Study not found returns 404
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import timedelta

from app.models.study import Study
from app.models.user import User
from app.models.document import Document
from app.models.csr import OutputDocument, OutputSection, OutputSectionVersion
from app.core.security import create_access_token
from app.core.config import settings


def get_auth_headers(user: User) -> dict:
    """Helper to create auth headers for a user."""
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    return {"Authorization": f"Bearer {access_token}"}


# Test Get Output Document
def test_member_can_get_output_document(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study
):
    """
    Test that a study member can successfully get an output document for a study.
    """
    headers = get_auth_headers(test_user)
    
    response = client.get(
        f"/api/v1/output/{test_study.id}",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["study_id"] == test_study.id
    assert "title" in data
    assert "status" in data
    assert "sections" in data
    assert isinstance(data["sections"], list)
    # Should have default sections created
    assert len(data["sections"]) > 0


def test_non_member_cannot_get_output_document(
    client: TestClient,
    db: Session,
    test_study: Study,
    other_user: User
):
    """
    Test that a non-member user receives 403 when trying to get an output document.
    """
    headers = get_auth_headers(other_user)
    
    response = client.get(
        f"/api/v1/output/{test_study.id}",
        headers=headers
    )
    
    assert response.status_code == 403


def test_get_output_document_study_not_found(
    client: TestClient,
    db: Session,
    test_user: User
):
    """
    Test that getting an output document for a non-existent study returns 404.
    """
    headers = get_auth_headers(test_user)
    
    response = client.get(
        "/api/v1/output/99999",
        headers=headers
    )
    
    assert response.status_code == 404


# Test Get Output Document by Document ID
def test_member_can_get_output_document_by_document_id(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study
):
    """
    Test that a study member can get an output document by document ID.
    """
    # Create a document of type "csr"
    document = Document(
        study_id=test_study.id,
        type="csr",
        title="Test CSR Document",
        status="draft",
        created_by=test_user.id,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    headers = get_auth_headers(test_user)
    
    response = client.get(
        f"/api/v1/output/document/{document.id}",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["study_id"] == test_study.id
    assert "sections" in data


def test_get_output_document_wrong_type(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study
):
    """
    Test that getting an output document for a non-csr document returns 400.
    """
    # Create a document of type "protocol" (not "csr")
    document = Document(
        study_id=test_study.id,
        type="protocol",
        title="Test Protocol Document",
        status="draft",
        created_by=test_user.id,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    headers = get_auth_headers(test_user)
    
    response = client.get(
        f"/api/v1/output/document/{document.id}",
        headers=headers
    )
    
    assert response.status_code == 400
    assert "csr" in response.json()["detail"].lower()


# Test Get Output Document Sections
def test_member_can_get_output_sections(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study
):
    """
    Test that a study member can successfully get output document sections.
    """
    headers = get_auth_headers(test_user)
    
    response = client.get(
        f"/api/v1/output/{test_study.id}/sections",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Should have default sections created
    assert len(data) > 0
    # Check section structure
    section = data[0]
    assert "id" in section
    assert "code" in section
    assert "title" in section
    assert "order_index" in section


# Test Get Latest Section Version
def test_member_can_get_latest_section_version(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study
):
    """
    Test that a study member can get the latest version of a section.
    """
    # First, get or create output document to ensure sections exist
    headers = get_auth_headers(test_user)
    
    response = client.get(
        f"/api/v1/output/{test_study.id}",
        headers=headers
    )
    assert response.status_code == 200
    sections = response.json()["sections"]
    assert len(sections) > 0
    section_id = sections[0]["id"]
    
    # Create a version for this section
    from app.models.csr import OutputSectionVersion
    version = OutputSectionVersion(
        section_id=section_id,
        text="Test section content",
        created_by=test_user.username,
        source="human",
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    
    # Get latest version
    response = client.get(
        f"/api/v1/output/sections/{section_id}/versions/latest",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == version.id
    assert data["text"] == "Test section content"
    assert data["source"] == "human"


def test_get_latest_section_version_not_found(
    client: TestClient,
    db: Session,
    test_user: User
):
    """
    Test that getting latest version for a non-existent section returns 404.
    """
    headers = get_auth_headers(test_user)
    
    response = client.get(
        "/api/v1/output/sections/99999/versions/latest",
        headers=headers
    )
    
    assert response.status_code == 404


# Test Create Section Version
def test_member_can_create_section_version(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study
):
    """
    Test that a study member can create a new section version.
    """
    # First, get or create output document to ensure sections exist
    headers = get_auth_headers(test_user)
    
    response = client.get(
        f"/api/v1/output/{test_study.id}",
        headers=headers
    )
    assert response.status_code == 200
    sections = response.json()["sections"]
    assert len(sections) > 0
    section_id = sections[0]["id"]
    
    # Create a new version
    version_data = {
        "text": "New section content",
        "created_by": test_user.username
    }
    
    response = client.post(
        f"/api/v1/output/sections/{section_id}/versions",
        json=version_data,
        headers=headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["text"] == "New section content"
    assert data["source"] == "human"
    assert "id" in data
    assert "created_at" in data


# Test Export Output Document to DOCX
def test_member_can_export_output_document_to_docx(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study
):
    """
    Test that a study member can export an output document to DOCX.
    """
    headers = get_auth_headers(test_user)
    
    response = client.get(
        f"/api/v1/output/{test_study.id}/export/docx",
        headers=headers
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert "attachment" in response.headers["content-disposition"]
    assert "filename" in response.headers["content-disposition"]
    # Check that we got binary content
    assert len(response.content) > 0
    # DOCX files start with PK (ZIP file signature)
    assert response.content[:2] == b"PK"

