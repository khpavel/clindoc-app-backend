"""
Unit tests for documents endpoints.

Tests that:
1. Study members can list documents for a study
2. Owner/editor can successfully create documents
3. Viewer cannot create documents (403)
4. Non-member cannot list or create documents (403)
5. Study not found returns 404
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.study import Study
from app.models.study_member import StudyMember
from app.models.user import User
from app.models.document import Document
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


# List documents tests

def test_member_can_list_documents(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study
):
    """
    Test that a study member can successfully list documents for a study.
    """
    # Create a document for the study
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
        f"/api/v1/studies/{test_study.id}/documents",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == document.id
    assert data[0]["type"] == "csr"
    assert data[0]["title"] == "Test CSR Document"
    assert data[0]["study_id"] == test_study.id


def test_non_member_cannot_list_documents(
    client: TestClient,
    db: Session,
    test_study: Study,
    other_user: User
):
    """
    Test that a non-member user receives 403 when trying to list documents.
    """
    # other_user is not a member of test_study
    headers = get_auth_headers(other_user)
    
    response = client.get(
        f"/api/v1/studies/{test_study.id}/documents",
        headers=headers
    )
    
    assert response.status_code == 403
    assert "member" in response.json()["detail"].lower() or "access denied" in response.json()["detail"].lower()


def test_list_documents_study_not_found(
    client: TestClient,
    db: Session,
    test_user: User
):
    """
    Test that listing documents for a non-existent study returns 404.
    """
    headers = get_auth_headers(test_user)
    nonexistent_study_id = 99999
    
    response = client.get(
        f"/api/v1/studies/{nonexistent_study_id}/documents",
        headers=headers
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_list_documents_ordered_by_type_then_created_at(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study
):
    """
    Test that documents are returned ordered by type first, then created_at ascending.
    """
    # Create multiple documents with different types and creation times
    doc1 = Document(
        study_id=test_study.id,
        type="csr",
        title="CSR Document 1",
        status="draft",
        created_by=test_user.id,
        created_at=datetime(2024, 1, 1, 10, 0, 0),
    )
    doc2 = Document(
        study_id=test_study.id,
        type="protocol",
        title="Protocol Document",
        status="draft",
        created_by=test_user.id,
        created_at=datetime(2024, 1, 1, 11, 0, 0),
    )
    doc3 = Document(
        study_id=test_study.id,
        type="ib",
        title="IB Document",
        status="draft",
        created_by=test_user.id,
        created_at=datetime(2024, 1, 1, 9, 0, 0),
    )
    doc4 = Document(
        study_id=test_study.id,
        type="csr",
        title="CSR Document 2",
        status="draft",
        created_by=test_user.id,
        created_at=datetime(2024, 1, 1, 8, 0, 0),
    )
    db.add_all([doc1, doc2, doc3, doc4])
    db.commit()
    
    headers = get_auth_headers(test_user)
    
    response = client.get(
        f"/api/v1/studies/{test_study.id}/documents",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 4
    # Should be ordered by type first (alphabetically: csr, ib, protocol), then created_at ascending
    assert data[0]["title"] == "CSR Document 2"  # csr, 8:00
    assert data[1]["title"] == "CSR Document 1"   # csr, 10:00
    assert data[2]["title"] == "IB Document"     # ib, 9:00
    assert data[3]["title"] == "Protocol Document"  # protocol, 11:00


# Create document tests

def test_owner_can_create_document(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study
):
    """
    Test that a study owner can successfully create a document.
    """
    headers = get_auth_headers(test_user)
    
    document_data = {
        "type": "csr",
        "title": "New CSR Document",
        "template_code": "csr_template_v1",
        "status": "draft"
    }
    
    response = client.post(
        f"/api/v1/studies/{test_study.id}/documents",
        headers=headers,
        json=document_data
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "csr"
    assert data["title"] == "New CSR Document"
    assert data["template_code"] == "csr_template_v1"
    assert data["status"] == "draft"
    assert data["study_id"] == test_study.id
    assert data["created_by"] == test_user.id
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    
    # Verify document was created in database
    document = db.query(Document).filter(Document.id == data["id"]).first()
    assert document is not None
    assert document.title == "New CSR Document"


def test_editor_can_create_document(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study,
    other_user: User
):
    """
    Test that a study editor can successfully create a document.
    """
    # Add other_user as editor
    editor_member = StudyMember(
        user_id=other_user.id,
        study_id=test_study.id,
        role="editor"
    )
    db.add(editor_member)
    db.commit()
    
    headers = get_auth_headers(other_user)
    
    document_data = {
        "type": "protocol",
        "title": "New Protocol Document",
        "status": "draft"
    }
    
    response = client.post(
        f"/api/v1/studies/{test_study.id}/documents",
        headers=headers,
        json=document_data
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "protocol"
    assert data["title"] == "New Protocol Document"
    assert data["created_by"] == other_user.id


def test_viewer_cannot_create_document(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study,
    other_user: User
):
    """
    Test that a study viewer receives 403 when trying to create a document.
    """
    # Add other_user as viewer
    viewer_member = StudyMember(
        user_id=other_user.id,
        study_id=test_study.id,
        role="viewer"
    )
    db.add(viewer_member)
    db.commit()
    
    headers = get_auth_headers(other_user)
    
    document_data = {
        "type": "csr",
        "title": "New Document",
        "status": "draft"
    }
    
    response = client.post(
        f"/api/v1/studies/{test_study.id}/documents",
        headers=headers,
        json=document_data
    )
    
    assert response.status_code == 403
    assert "owner" in response.json()["detail"].lower() or "editor" in response.json()["detail"].lower()
    
    # Verify document was NOT created
    count = db.query(Document).filter(Document.study_id == test_study.id).count()
    assert count == 0


def test_non_member_cannot_create_document(
    client: TestClient,
    db: Session,
    test_study: Study,
    other_user: User
):
    """
    Test that a non-member user receives 403 when trying to create a document.
    """
    # other_user is not a member of test_study
    headers = get_auth_headers(other_user)
    
    document_data = {
        "type": "csr",
        "title": "New Document",
        "status": "draft"
    }
    
    response = client.post(
        f"/api/v1/studies/{test_study.id}/documents",
        headers=headers,
        json=document_data
    )
    
    assert response.status_code == 403
    assert "member" in response.json()["detail"].lower() or "access denied" in response.json()["detail"].lower()
    
    # Verify document was NOT created
    count = db.query(Document).filter(Document.study_id == test_study.id).count()
    assert count == 0


def test_create_document_study_not_found(
    client: TestClient,
    db: Session,
    test_user: User
):
    """
    Test that creating a document for a non-existent study returns 404.
    """
    headers = get_auth_headers(test_user)
    nonexistent_study_id = 99999
    
    document_data = {
        "type": "csr",
        "title": "New Document",
        "status": "draft"
    }
    
    response = client.post(
        f"/api/v1/studies/{nonexistent_study_id}/documents",
        headers=headers,
        json=document_data
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_create_document_defaults_status_to_draft(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study
):
    """
    Test that creating a document without specifying status defaults to "draft".
    """
    headers = get_auth_headers(test_user)
    
    document_data = {
        "type": "csr",
        "title": "New Document"
        # status not provided
    }
    
    response = client.post(
        f"/api/v1/studies/{test_study.id}/documents",
        headers=headers,
        json=document_data
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "draft"


def test_create_document_sets_created_by(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study
):
    """
    Test that creating a document automatically sets created_by to the current user.
    """
    headers = get_auth_headers(test_user)
    
    document_data = {
        "type": "csr",
        "title": "New Document",
        "status": "draft"
    }
    
    response = client.post(
        f"/api/v1/studies/{test_study.id}/documents",
        headers=headers,
        json=document_data
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["created_by"] == test_user.id
    
    # Verify in database
    document = db.query(Document).filter(Document.id == data["id"]).first()
    assert document.created_by == test_user.id


def test_create_document_with_optional_fields(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study
):
    """
    Test that creating a document with optional fields works correctly.
    """
    headers = get_auth_headers(test_user)
    
    document_data = {
        "type": "protocol",
        "title": "Protocol Document",
        "template_code": "protocol_template_v2",
        "status": "in_qc",
        "current_version_label": "v1.0"
    }
    
    response = client.post(
        f"/api/v1/studies/{test_study.id}/documents",
        headers=headers,
        json=document_data
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["template_code"] == "protocol_template_v2"
    assert data["status"] == "in_qc"
    assert data["current_version_label"] == "v1.0"


def test_list_documents_ensure_default_csr_creates_document(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study
):
    """
    Test that ensure_default_csr=true creates a default CSR document if none exists.
    """
    headers = get_auth_headers(test_user)
    
    # Verify no documents exist initially
    response = client.get(
        f"/api/v1/studies/{test_study.id}/documents",
        headers=headers
    )
    assert response.status_code == 200
    assert len(response.json()) == 0
    
    # Request with ensure_default_csr=true
    response = client.get(
        f"/api/v1/studies/{test_study.id}/documents?ensure_default_csr=true",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["type"] == "csr"
    assert data[0]["status"] == "draft"
    assert data[0]["created_by"] == test_user.id
    assert "CSR" in data[0]["title"]
    assert str(test_study.code) in data[0]["title"] or str(test_study.id) in data[0]["title"]
    
    # Verify document was created in database
    document = db.query(Document).filter(
        Document.study_id == test_study.id,
        Document.type == "csr"
    ).first()
    assert document is not None
    assert document.status == "draft"
    assert document.created_by == test_user.id


def test_list_documents_ensure_default_csr_does_not_duplicate(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study
):
    """
    Test that ensure_default_csr=true does not create a duplicate if CSR document already exists.
    """
    headers = get_auth_headers(test_user)
    
    # Create an existing CSR document
    existing_csr = Document(
        study_id=test_study.id,
        type="csr",
        title="Existing CSR",
        status="in_qc",
        created_by=test_user.id,
    )
    db.add(existing_csr)
    db.commit()
    db.refresh(existing_csr)
    
    # Request with ensure_default_csr=true
    response = client.get(
        f"/api/v1/studies/{test_study.id}/documents?ensure_default_csr=true",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == existing_csr.id
    assert data[0]["title"] == "Existing CSR"
    assert data[0]["status"] == "in_qc"  # Should not be changed
    
    # Verify no duplicate was created
    csr_count = db.query(Document).filter(
        Document.study_id == test_study.id,
        Document.type == "csr"
    ).count()
    assert csr_count == 1


def test_create_document_validates_type(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study
):
    """
    Test that creating a document with an invalid type returns 400.
    """
    headers = get_auth_headers(test_user)
    
    document_data = {
        "type": "invalid_type",
        "title": "Test Document",
        "status": "draft"
    }
    
    response = client.post(
        f"/api/v1/studies/{test_study.id}/documents",
        headers=headers,
        json=document_data
    )
    
    assert response.status_code == 422  # Validation error
    assert "type" in str(response.json()).lower()


def test_create_document_validates_status(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study
):
    """
    Test that creating a document with an invalid status returns 400.
    """
    headers = get_auth_headers(test_user)
    
    document_data = {
        "type": "csr",
        "title": "Test Document",
        "status": "invalid_status"
    }
    
    response = client.post(
        f"/api/v1/studies/{test_study.id}/documents",
        headers=headers,
        json=document_data
    )
    
    assert response.status_code == 422  # Validation error
    assert "status" in str(response.json()).lower()

