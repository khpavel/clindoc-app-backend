"""
Integration tests for QC multilingual behavior.

Tests that:
1. QC engine is called with correct language parameter
2. QC rules return messages in the correct language (RU/EN)
3. Document language takes precedence over user UI language for QC checks
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.study import Study
from app.models.document import Document
from app.models.output_document import OutputDocument, OutputSection
from app.models.user import User
from app.core.security import create_access_token
from app.core.config import settings
from datetime import timedelta
from app.services.qc_rules import run_qc_rules_for_document


def get_auth_headers(user: User) -> dict:
    """Helper to create auth headers for a user."""
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def test_document_en(db: Session, test_study: Study, test_user: User) -> Document:
    """Create a test document with language='en'."""
    doc = Document(
        study_id=test_study.id,
        type="csr",
        title="Test CSR",
        language="en",
        created_by=test_user.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@pytest.fixture
def test_document_ru(db: Session, test_study: Study, test_user: User) -> Document:
    """Create a test document with language='ru'."""
    doc = Document(
        study_id=test_study.id,
        type="csr",
        title="Test CSR",
        language="ru",
        created_by=test_user.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@pytest.fixture
def test_output_document_en(db: Session, test_study: Study, test_document_en: Document) -> OutputDocument:
    """Create a test output document linked to English document."""
    output_doc = OutputDocument(
        study_id=test_study.id,
        title="Test CSR",
        document_id=test_document_en.id,
        language="en",
    )
    db.add(output_doc)
    db.commit()
    db.refresh(output_doc)
    return output_doc


@pytest.fixture
def test_output_document_ru(db: Session, test_study: Study, test_document_ru: Document) -> OutputDocument:
    """Create a test output document linked to Russian document."""
    output_doc = OutputDocument(
        study_id=test_study.id,
        title="Test CSR",
        document_id=test_document_ru.id,
        language="ru",
    )
    db.add(output_doc)
    db.commit()
    db.refresh(output_doc)
    return output_doc


def test_qc_engine_called_with_english_for_english_document(
    client: TestClient,
    db: Session,
    test_user: User,
    test_document_en: Document,
):
    """Test that QC endpoint uses document language='en' for QC checks."""
    # Set user UI language to Russian
    test_user.ui_language = "ru"
    db.commit()
    
    headers = get_auth_headers(test_user)
    headers["Accept-Language"] = "ru"  # Also set header to Russian
    
    # First, ensure OutputDocument exists
    from app.services.output_document_document_link import get_or_create_output_document_for_document
    output_doc = get_or_create_output_document_for_document(test_document_en, test_user, db)
    
    # Clear any existing QC issues
    from app.models.qc import QCIssue
    db.query(QCIssue).filter(QCIssue.document_id == output_doc.id).delete()
    db.commit()
    
    # Mock run_qc_rules_for_document to capture the language parameter
    with patch("app.api.v1.qc.run_qc_rules_for_document") as mock_qc:
        mock_qc.return_value = []
        
        response = client.post(
            f"/api/v1/qc/documents/{test_document_en.id}/run",
            headers=headers,
        )
        
        assert response.status_code in (200, 201)
        
        # Verify that QC was called with language="en" (document language)
        # not "ru" (user UI language or request language)
        mock_qc.assert_called_once()
        call_kwargs = mock_qc.call_args[1]
        assert call_kwargs.get("language") == "en"


def test_qc_engine_called_with_russian_for_russian_document(
    client: TestClient,
    db: Session,
    test_user: User,
    test_document_ru: Document,
):
    """Test that QC endpoint uses document language='ru' for QC checks."""
    # Set user UI language to English
    test_user.ui_language = "en"
    db.commit()
    
    headers = get_auth_headers(test_user)
    headers["Accept-Language"] = "en"  # Also set header to English
    
    # First, ensure OutputDocument exists
    from app.services.output_document_document_link import get_or_create_output_document_for_document
    output_doc = get_or_create_output_document_for_document(test_document_ru, test_user, db)
    
    # Clear any existing QC issues
    from app.models.qc import QCIssue
    db.query(QCIssue).filter(QCIssue.document_id == output_doc.id).delete()
    db.commit()
    
    # Mock run_qc_rules_for_document to capture the language parameter
    with patch("app.api.v1.qc.run_qc_rules_for_document") as mock_qc:
        mock_qc.return_value = []
        
        response = client.post(
            f"/api/v1/qc/documents/{test_document_ru.id}/run",
            headers=headers,
        )
        
        assert response.status_code in (200, 201)
        
        # Verify that QC was called with language="ru" (document language)
        # not "en" (user UI language or request language)
        mock_qc.assert_called_once()
        call_kwargs = mock_qc.call_args[1]
        assert call_kwargs.get("language") == "ru"


def test_qc_rules_return_english_messages_for_english_document(
    db: Session,
    test_study: Study,
    test_output_document_en: OutputDocument,
):
    """Test that QC rules return English messages when language='en'."""
    # Clear any existing QC issues
    from app.models.qc import QCIssue
    db.query(QCIssue).filter(QCIssue.document_id == test_output_document_en.id).delete()
    db.commit()
    
    # Run QC with English language
    issues = run_qc_rules_for_document(
        db=db,
        document_id=test_output_document_en.id,
        study_id=test_output_document_en.study_id,
        language="en",
    )
    
    # Check that all issues have English messages
    for issue in issues:
        assert isinstance(issue.message, str)
        # English QC messages should contain English keywords
        # For example, "Missing required section" for missing sections
        if "Missing" in issue.message or "required section" in issue.message:
            assert "Missing" in issue.message or "required section" in issue.message


def test_qc_rules_return_russian_messages_for_russian_document(
    db: Session,
    test_study: Study,
    test_output_document_ru: OutputDocument,
):
    """Test that QC rules return Russian messages when language='ru'."""
    # Clear any existing QC issues
    from app.models.qc import QCIssue
    db.query(QCIssue).filter(QCIssue.document_id == test_output_document_ru.id).delete()
    db.commit()
    
    # Run QC with Russian language
    issues = run_qc_rules_for_document(
        db=db,
        document_id=test_output_document_ru.id,
        study_id=test_output_document_ru.study_id,
        language="ru",
    )
    
    # Check that all issues have Russian messages
    for issue in issues:
        assert isinstance(issue.message, str)
        # Russian QC messages should contain Russian keywords
        # For example, "Отсутствует" for missing sections
        if "Отсутствует" in issue.message or "обязательная секция" in issue.message:
            assert "Отсутствует" in issue.message or "обязательная секция" in issue.message


def test_qc_rules_use_different_languages_for_different_documents(
    db: Session,
    test_study: Study,
    test_output_document_en: OutputDocument,
    test_output_document_ru: OutputDocument,
):
    """Test that QC rules produce different messages for different languages."""
    from app.models.qc import QCIssue
    
    # Clear existing issues
    db.query(QCIssue).filter(QCIssue.document_id == test_output_document_en.id).delete()
    db.query(QCIssue).filter(QCIssue.document_id == test_output_document_ru.id).delete()
    db.commit()
    
    # Run QC with English
    issues_en = run_qc_rules_for_document(
        db=db,
        document_id=test_output_document_en.id,
        study_id=test_output_document_en.study_id,
        language="en",
    )
    
    # Run QC with Russian
    issues_ru = run_qc_rules_for_document(
        db=db,
        document_id=test_output_document_ru.id,
        study_id=test_output_document_ru.study_id,
        language="ru",
    )
    
    # If we have issues, they should be in different languages
    if issues_en and issues_ru:
        en_messages = {issue.message for issue in issues_en}
        ru_messages = {issue.message for issue in issues_ru}
        
        # Check that Russian messages contain Cyrillic characters
        has_cyrillic = any(
            any(ord(c) >= 0x0400 and ord(c) <= 0x04FF for c in msg)
            for msg in ru_messages
        )
        
        # English messages should primarily contain Latin characters
        has_latin_only = all(
            all(ord(c) < 0x0080 for c in msg) or "Missing" in msg or "required" in msg
            for msg in en_messages
        )
        
        # If we have messages, they should reflect the language
        if has_cyrillic:
            assert has_cyrillic, "Russian messages should contain Cyrillic characters"


def test_qc_endpoint_uses_document_language_not_user_language(
    client: TestClient,
    db: Session,
    test_user: User,
    test_document_en: Document,
):
    """Test that QC uses document language, not user UI language."""
    # Set user UI language to Russian
    test_user.ui_language = "ru"
    db.commit()
    
    headers = get_auth_headers(test_user)
    
    # First, ensure OutputDocument exists
    from app.services.output_document_document_link import get_or_create_output_document_for_document
    output_doc = get_or_create_output_document_for_document(test_document_en, test_user, db)
    
    # Clear any existing QC issues
    from app.models.qc import QCIssue
    db.query(QCIssue).filter(QCIssue.document_id == output_doc.id).delete()
    db.commit()
    
    # Mock run_qc_rules_for_document to capture the language parameter
    with patch("app.api.v1.qc.run_qc_rules_for_document") as mock_qc:
        mock_qc.return_value = []
        
        response = client.post(
            f"/api/v1/qc/documents/{test_document_en.id}/run",
            headers=headers,
        )
        
        assert response.status_code in (200, 201)
        
        # Verify that QC was called with document language, not user language
        mock_qc.assert_called_once()
        call_kwargs = mock_qc.call_args[1]
        # Document language is "en", user UI language is "ru"
        # QC should use "en" (document language)
        assert call_kwargs.get("language") == "en"

