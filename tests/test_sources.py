"""
Unit tests for source documents endpoints.

Tests that:
1. Owner/editor can successfully delete source documents
2. Viewer receives 403 Forbidden when trying to delete
3. Non-member receives 403 Forbidden
4. Deleting non-existent document returns 404
5. Soft delete sets correct fields and removes RAG chunks
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.study import Study
from app.models.study_member import StudyMember
from app.models.user import User
from app.models.source import SourceDocument
from app.models.rag import RagChunk
from app.core.security import create_access_token
from app.core.config import settings
from datetime import timedelta, datetime


def get_auth_headers(user: User) -> dict:
    """Helper to create auth headers for a user."""
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def source_document(db: Session, test_study: Study, test_user: User) -> SourceDocument:
    """Create a test source document."""
    source_doc = SourceDocument(
        study_id=test_study.id,
        type="protocol",
        file_name="test_protocol.pdf",
        storage_path=f"study_{test_study.id}/test_protocol.pdf",
        uploaded_at=datetime.utcnow(),
        uploaded_by=test_user.username,
        language="ru",
        status="active",
        is_current=True,
        is_rag_enabled=True,
        index_status="indexed"
    )
    db.add(source_doc)
    db.commit()
    db.refresh(source_doc)
    return source_doc


@pytest.fixture
def rag_chunk(db: Session, source_document: SourceDocument) -> RagChunk:
    """Create a test RAG chunk for the source document."""
    chunk = RagChunk(
        study_id=source_document.study_id,
        source_document_id=source_document.id,
        source_type=source_document.type,
        order_index=0,
        text="Test chunk text"
    )
    db.add(chunk)
    db.commit()
    db.refresh(chunk)
    return chunk


# DELETE endpoint tests

def test_owner_can_delete_source_document(
    client: TestClient,
    db: Session,
    test_user: User,
    source_document: SourceDocument
):
    """
    Test that a study owner can successfully delete a source document.
    """
    headers = get_auth_headers(test_user)
    
    response = client.delete(
        f"/api/v1/sources/{source_document.id}",
        headers=headers
    )
    
    assert response.status_code == 204
    
    # Verify soft delete: document still exists but with archived status
    db.refresh(source_document)
    assert source_document.status == "archived"
    assert source_document.is_current is False
    assert source_document.is_rag_enabled is False
    assert source_document.index_status == "not_indexed"


def test_editor_can_delete_source_document(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study,
    other_user: User,
    source_document: SourceDocument
):
    """
    Test that a study editor can successfully delete a source document.
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
    
    response = client.delete(
        f"/api/v1/sources/{source_document.id}",
        headers=headers
    )
    
    assert response.status_code == 204
    
    # Verify soft delete
    db.refresh(source_document)
    assert source_document.status == "archived"
    assert source_document.is_current is False
    assert source_document.is_rag_enabled is False


def test_viewer_cannot_delete_source_document(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study,
    other_user: User,
    source_document: SourceDocument
):
    """
    Test that a study viewer receives 403 when trying to delete a source document.
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
    
    response = client.delete(
        f"/api/v1/sources/{source_document.id}",
        headers=headers
    )
    
    assert response.status_code == 403
    assert "owner" in response.json()["detail"].lower() or "editor" in response.json()["detail"].lower()
    
    # Verify document was NOT deleted
    db.refresh(source_document)
    assert source_document.status == "active"
    assert source_document.is_current is True


def test_non_member_cannot_delete_source_document(
    client: TestClient,
    db: Session,
    test_study: Study,
    other_user: User,
    source_document: SourceDocument
):
    """
    Test that a non-member user receives 403 when trying to delete a source document.
    """
    # other_user is not a member of test_study
    headers = get_auth_headers(other_user)
    
    response = client.delete(
        f"/api/v1/sources/{source_document.id}",
        headers=headers
    )
    
    assert response.status_code == 403
    assert "member" in response.json()["detail"].lower() or "access denied" in response.json()["detail"].lower()
    
    # Verify document was NOT deleted
    db.refresh(source_document)
    assert source_document.status == "active"


def test_delete_nonexistent_source_document_returns_404(
    client: TestClient,
    db: Session,
    test_user: User
):
    """
    Test that attempting to delete a non-existent source document returns 404.
    """
    headers = get_auth_headers(test_user)
    nonexistent_doc_id = 99999
    
    response = client.delete(
        f"/api/v1/sources/{nonexistent_doc_id}",
        headers=headers
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_delete_source_document_removes_rag_chunks(
    client: TestClient,
    db: Session,
    test_user: User,
    source_document: SourceDocument,
    rag_chunk: RagChunk
):
    """
    Test that deleting a source document removes associated RAG chunks.
    """
    # Verify chunk exists before deletion
    chunk_before = db.query(RagChunk).filter(RagChunk.id == rag_chunk.id).first()
    assert chunk_before is not None
    
    headers = get_auth_headers(test_user)
    
    response = client.delete(
        f"/api/v1/sources/{source_document.id}",
        headers=headers
    )
    
    assert response.status_code == 204
    
    # Verify chunk was deleted
    chunk_after = db.query(RagChunk).filter(RagChunk.id == rag_chunk.id).first()
    assert chunk_after is None
    
    # Verify document was soft deleted
    db.refresh(source_document)
    assert source_document.status == "archived"
    assert source_document.is_rag_enabled is False


def test_delete_source_document_with_multiple_rag_chunks(
    client: TestClient,
    db: Session,
    test_user: User,
    source_document: SourceDocument
):
    """
    Test that deleting a source document removes all associated RAG chunks.
    """
    # Create multiple RAG chunks
    chunks = []
    for i in range(3):
        chunk = RagChunk(
            study_id=source_document.study_id,
            source_document_id=source_document.id,
            source_type=source_document.type,
            order_index=i,
            text=f"Test chunk {i}"
        )
        chunks.append(chunk)
        db.add(chunk)
    db.commit()
    
    # Verify chunks exist
    chunk_count_before = db.query(RagChunk).filter(
        RagChunk.source_document_id == source_document.id
    ).count()
    assert chunk_count_before == 3
    
    headers = get_auth_headers(test_user)
    
    response = client.delete(
        f"/api/v1/sources/{source_document.id}",
        headers=headers
    )
    
    assert response.status_code == 204
    
    # Verify all chunks were deleted
    chunk_count_after = db.query(RagChunk).filter(
        RagChunk.source_document_id == source_document.id
    ).count()
    assert chunk_count_after == 0


# Permanent DELETE endpoint tests

def test_owner_can_permanently_delete_source_document(
    client: TestClient,
    db: Session,
    test_user: User,
    source_document: SourceDocument
):
    """
    Test that a study owner can permanently delete a source document.
    """
    headers = get_auth_headers(test_user)
    
    source_doc_id = source_document.id
    
    response = client.delete(
        f"/api/v1/sources/{source_doc_id}/permanent",
        headers=headers
    )
    
    assert response.status_code == 204
    
    # Verify document was permanently deleted (not in DB)
    deleted_doc = db.query(SourceDocument).filter(SourceDocument.id == source_doc_id).first()
    assert deleted_doc is None


def test_editor_cannot_permanently_delete_source_document(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study,
    other_user: User,
    source_document: SourceDocument
):
    """
    Test that a study editor receives 403 when trying to permanently delete a source document.
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
    
    response = client.delete(
        f"/api/v1/sources/{source_document.id}/permanent",
        headers=headers
    )
    
    assert response.status_code == 403
    assert "owner" in response.json()["detail"].lower()
    
    # Verify document was NOT deleted
    db.refresh(source_document)
    assert source_document.id is not None


def test_viewer_cannot_permanently_delete_source_document(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study,
    other_user: User,
    source_document: SourceDocument
):
    """
    Test that a study viewer receives 403 when trying to permanently delete a source document.
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
    
    response = client.delete(
        f"/api/v1/sources/{source_document.id}/permanent",
        headers=headers
    )
    
    assert response.status_code == 403
    assert "owner" in response.json()["detail"].lower()
    
    # Verify document was NOT deleted
    db.refresh(source_document)
    assert source_document.id is not None


def test_non_member_cannot_permanently_delete_source_document(
    client: TestClient,
    db: Session,
    test_study: Study,
    other_user: User,
    source_document: SourceDocument
):
    """
    Test that a non-member user receives 403 when trying to permanently delete a source document.
    """
    # other_user is not a member of test_study
    headers = get_auth_headers(other_user)
    
    response = client.delete(
        f"/api/v1/sources/{source_document.id}/permanent",
        headers=headers
    )
    
    assert response.status_code == 403
    assert "member" in response.json()["detail"].lower() or "access denied" in response.json()["detail"].lower()
    
    # Verify document was NOT deleted
    db.refresh(source_document)
    assert source_document.id is not None


def test_permanent_delete_nonexistent_source_document_returns_404(
    client: TestClient,
    db: Session,
    test_user: User
):
    """
    Test that attempting to permanently delete a non-existent source document returns 404.
    """
    headers = get_auth_headers(test_user)
    nonexistent_doc_id = 99999
    
    response = client.delete(
        f"/api/v1/sources/{nonexistent_doc_id}/permanent",
        headers=headers
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_permanent_delete_removes_rag_chunks(
    client: TestClient,
    db: Session,
    test_user: User,
    source_document: SourceDocument,
    rag_chunk: RagChunk
):
    """
    Test that permanently deleting a source document removes associated RAG chunks.
    """
    # Verify chunk exists before deletion
    chunk_before = db.query(RagChunk).filter(RagChunk.id == rag_chunk.id).first()
    assert chunk_before is not None
    
    headers = get_auth_headers(test_user)
    source_doc_id = source_document.id
    
    response = client.delete(
        f"/api/v1/sources/{source_doc_id}/permanent",
        headers=headers
    )
    
    assert response.status_code == 204
    
    # Verify chunk was deleted
    chunk_after = db.query(RagChunk).filter(RagChunk.id == rag_chunk.id).first()
    assert chunk_after is None
    
    # Verify document was permanently deleted
    deleted_doc = db.query(SourceDocument).filter(SourceDocument.id == source_doc_id).first()
    assert deleted_doc is None


def test_permanent_delete_removes_all_rag_chunks(
    client: TestClient,
    db: Session,
    test_user: User,
    source_document: SourceDocument
):
    """
    Test that permanently deleting a source document removes all associated RAG chunks.
    """
    # Create multiple RAG chunks
    chunks = []
    for i in range(3):
        chunk = RagChunk(
            study_id=source_document.study_id,
            source_document_id=source_document.id,
            source_type=source_document.type,
            order_index=i,
            text=f"Test chunk {i}"
        )
        chunks.append(chunk)
        db.add(chunk)
    db.commit()
    
    # Verify chunks exist
    chunk_count_before = db.query(RagChunk).filter(
        RagChunk.source_document_id == source_document.id
    ).count()
    assert chunk_count_before == 3
    
    headers = get_auth_headers(test_user)
    source_doc_id = source_document.id
    
    response = client.delete(
        f"/api/v1/sources/{source_doc_id}/permanent",
        headers=headers
    )
    
    assert response.status_code == 204
    
    # Verify all chunks were deleted
    chunk_count_after = db.query(RagChunk).filter(
        RagChunk.source_document_id == source_document.id
    ).count()
    assert chunk_count_after == 0
    
    # Verify document was permanently deleted
    deleted_doc = db.query(SourceDocument).filter(SourceDocument.id == source_doc_id).first()
    assert deleted_doc is None


# RESTORE endpoint tests

@pytest.fixture
def archived_source_document(db: Session, test_study: Study, test_user: User) -> SourceDocument:
    """Create an archived test source document."""
    source_doc = SourceDocument(
        study_id=test_study.id,
        type="protocol",
        file_name="archived_protocol.pdf",
        storage_path=f"study_{test_study.id}/archived_protocol.pdf",
        uploaded_at=datetime.utcnow(),
        uploaded_by=test_user.username,
        language="ru",
        status="archived",
        is_current=False,
        is_rag_enabled=False,
        index_status="not_indexed"
    )
    db.add(source_doc)
    db.commit()
    db.refresh(source_doc)
    return source_doc


def test_owner_can_restore_source_document(
    client: TestClient,
    db: Session,
    test_user: User,
    archived_source_document: SourceDocument
):
    """
    Test that a study owner can successfully restore an archived source document.
    """
    headers = get_auth_headers(test_user)
    
    response = client.post(
        f"/api/v1/sources/{archived_source_document.id}/restore",
        headers=headers
    )
    
    assert response.status_code == 200
    
    # Verify restore
    db.refresh(archived_source_document)
    assert archived_source_document.status == "active"
    assert archived_source_document.is_rag_enabled is True
    assert archived_source_document.index_status == "not_indexed"
    # is_current should be True when no other active docs exist
    assert archived_source_document.is_current is True
    
    # Verify response data
    data = response.json()
    assert data["id"] == archived_source_document.id
    assert data["status"] == "active"
    assert data["is_rag_enabled"] is True
    assert data["index_status"] == "not_indexed"


def test_editor_can_restore_source_document(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study,
    other_user: User,
    archived_source_document: SourceDocument
):
    """
    Test that a study editor can successfully restore an archived source document.
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
    
    response = client.post(
        f"/api/v1/sources/{archived_source_document.id}/restore",
        headers=headers
    )
    
    assert response.status_code == 200
    
    # Verify restore
    db.refresh(archived_source_document)
    assert archived_source_document.status == "active"
    assert archived_source_document.is_rag_enabled is True
    assert archived_source_document.index_status == "not_indexed"


def test_viewer_cannot_restore_source_document(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study,
    other_user: User,
    archived_source_document: SourceDocument
):
    """
    Test that a study viewer receives 403 when trying to restore a source document.
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
    
    response = client.post(
        f"/api/v1/sources/{archived_source_document.id}/restore",
        headers=headers
    )
    
    assert response.status_code == 403
    assert "owner" in response.json()["detail"].lower() or "editor" in response.json()["detail"].lower()
    
    # Verify document was NOT restored
    db.refresh(archived_source_document)
    assert archived_source_document.status == "archived"
    assert archived_source_document.is_rag_enabled is False


def test_non_member_cannot_restore_source_document(
    client: TestClient,
    db: Session,
    test_study: Study,
    other_user: User,
    archived_source_document: SourceDocument
):
    """
    Test that a non-member user receives 403 when trying to restore a source document.
    """
    # other_user is not a member of test_study
    headers = get_auth_headers(other_user)
    
    response = client.post(
        f"/api/v1/sources/{archived_source_document.id}/restore",
        headers=headers
    )
    
    assert response.status_code == 403
    assert "member" in response.json()["detail"].lower() or "access denied" in response.json()["detail"].lower()
    
    # Verify document was NOT restored
    db.refresh(archived_source_document)
    assert archived_source_document.status == "archived"


def test_restore_nonexistent_source_document_returns_404(
    client: TestClient,
    db: Session,
    test_user: User
):
    """
    Test that attempting to restore a non-existent source document returns 404.
    """
    headers = get_auth_headers(test_user)
    nonexistent_doc_id = 99999
    
    response = client.post(
        f"/api/v1/sources/{nonexistent_doc_id}/restore",
        headers=headers
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_restore_non_archived_document_returns_400(
    client: TestClient,
    db: Session,
    test_user: User,
    source_document: SourceDocument
):
    """
    Test that attempting to restore a document that is not archived returns 400.
    """
    # source_document fixture has status="active"
    headers = get_auth_headers(test_user)
    
    response = client.post(
        f"/api/v1/sources/{source_document.id}/restore",
        headers=headers
    )
    
    assert response.status_code == 400
    assert "not archived" in response.json()["detail"].lower()
    
    # Verify document status unchanged
    db.refresh(source_document)
    assert source_document.status == "active"


def test_restore_sets_is_current_true_when_no_other_active_docs(
    client: TestClient,
    db: Session,
    test_user: User,
    archived_source_document: SourceDocument
):
    """
    Test that restoring a document sets is_current=True when no other active documents
    of the same (study_id, type, language) exist.
    """
    headers = get_auth_headers(test_user)
    
    response = client.post(
        f"/api/v1/sources/{archived_source_document.id}/restore",
        headers=headers
    )
    
    assert response.status_code == 200
    
    # Verify restore
    db.refresh(archived_source_document)
    assert archived_source_document.status == "active"
    # Since there are no other active docs, is_current should be True
    assert archived_source_document.is_current is True


def test_restore_sets_is_current_false_when_other_active_docs_exist(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study,
    archived_source_document: SourceDocument
):
    """
    Test that restoring a document sets is_current=False when other active documents
    of the same (study_id, type, language) exist.
    """
    # Create another active document with same (study_id, type, language)
    other_doc = SourceDocument(
        study_id=test_study.id,
        type=archived_source_document.type,
        file_name="other_protocol.pdf",
        storage_path=f"study_{test_study.id}/other_protocol.pdf",
        uploaded_at=datetime.utcnow(),
        uploaded_by=test_user.username,
        language=archived_source_document.language,
        status="active",
        is_current=True,
        is_rag_enabled=True,
        index_status="indexed"
    )
    db.add(other_doc)
    db.commit()
    
    headers = get_auth_headers(test_user)
    
    response = client.post(
        f"/api/v1/sources/{archived_source_document.id}/restore",
        headers=headers
    )
    
    assert response.status_code == 200
    
    # Verify restore
    db.refresh(archived_source_document)
    assert archived_source_document.status == "active"
    # Since there is another active doc, is_current should be False
    assert archived_source_document.is_current is False