"""
Integration tests for AI multilingual behavior.

Tests that:
1. AI prompt builder includes language instructions in the prompt
2. Language is correctly passed through the AI generation flow
3. Document language takes precedence over user UI language for content generation
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.study import Study
from app.models.output_document import OutputDocument, OutputSection
from app.models.document import Document
from app.models.user import User
from app.core.security import create_access_token
from app.core.config import settings
from datetime import timedelta
from app.services.ai_prompt_builder import build_generate_section_prompt


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


@pytest.fixture
def test_section_en(db: Session, test_output_document_en: OutputDocument) -> OutputSection:
    """Create a test section for English document."""
    section = OutputSection(
        document_id=test_output_document_en.id,
        code="SYNOPSIS",
        title="Synopsis",
        order_index=1,
    )
    db.add(section)
    db.commit()
    db.refresh(section)
    return section


@pytest.fixture
def test_section_ru(db: Session, test_output_document_ru: OutputDocument) -> OutputSection:
    """Create a test section for Russian document."""
    section = OutputSection(
        document_id=test_output_document_ru.id,
        code="SYNOPSIS",
        title="Synopsis",
        order_index=1,
    )
    db.add(section)
    db.commit()
    db.refresh(section)
    return section


def test_ai_prompt_builder_includes_english_instruction():
    """Test that prompt builder includes instruction to answer in English for language='en'."""
    study = MagicMock(spec=Study)
    study.title = "Test Study"
    study.code = "TEST-001"
    study.phase = None
    study.indication = None
    study.sponsor_name = None
    
    section = MagicMock(spec=OutputSection)
    section.title = "Synopsis"
    section.code = "SYNOPSIS"
    
    prompt = build_generate_section_prompt(
        study=study,
        section=section,
        current_text=None,
        rag_context_by_source_type={},
        user_prompt=None,
        language="en",
    )
    
    # Assert that the prompt includes instruction to write in English
    assert "Write in English, using medical terminology" in prompt
    assert "You are an expert" in prompt  # English system message
    assert "English" in prompt


def test_ai_prompt_builder_includes_russian_instruction():
    """Test that prompt builder includes instruction to answer in Russian for language='ru'."""
    study = MagicMock(spec=Study)
    study.title = "Test Study"
    study.code = "TEST-001"
    study.phase = None
    study.indication = None
    study.sponsor_name = None
    
    section = MagicMock(spec=OutputSection)
    section.title = "Synopsis"
    section.code = "SYNOPSIS"
    
    prompt = build_generate_section_prompt(
        study=study,
        section=section,
        current_text=None,
        rag_context_by_source_type={},
        user_prompt=None,
        language="ru",
    )
    
    # Assert that the prompt includes instruction to write in Russian
    assert "Пиши на русском языке, используя медицинскую терминологию" in prompt
    assert "Ты — эксперт" in prompt  # Russian system message
    assert "русском языке" in prompt


def test_ai_endpoint_uses_document_language_for_english(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study,
    test_document_en: Document,
    test_output_document_en: OutputDocument,
    test_section_en: OutputSection,
):
    """Test that AI endpoint uses document language='en' even if user UI language is 'ru'."""
    # Set user UI language to Russian
    test_user.ui_language = "ru"
    db.commit()
    
    headers = get_auth_headers(test_user)
    headers["Accept-Language"] = "ru"  # Also set header to Russian
    
    # Mock the AI client
    with patch("app.api.v1.ai.generate_section_text_stub", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = ("Generated text", "test-model")
        
        # Mock the prompt builder to capture the language parameter
        with patch("app.api.v1.ai.build_generate_section_prompt") as mock_prompt_builder:
            mock_prompt_builder.return_value = "Test prompt"
            
            response = client.post(
                "/api/v1/ai/generate-section-text",
                json={
                    "study_id": test_study.id,
                    "section_id": test_section_en.id,
                },
                headers=headers,
            )
            
            assert response.status_code == 200
            
            # Verify that prompt builder was called with language="en" (document language)
            # not "ru" (user UI language or request language)
            call_kwargs = mock_prompt_builder.call_args[1]
            assert call_kwargs.get("language") == "en"


def test_ai_endpoint_uses_document_language_for_russian(
    client: TestClient,
    db: Session,
    test_user: User,
    test_study: Study,
    test_document_ru: Document,
    test_output_document_ru: OutputDocument,
    test_section_ru: OutputSection,
):
    """Test that AI endpoint uses document language='ru' even if user UI language is 'en'."""
    # Set user UI language to English
    test_user.ui_language = "en"
    db.commit()
    
    headers = get_auth_headers(test_user)
    headers["Accept-Language"] = "en"  # Also set header to English
    
    # Mock the AI client
    with patch("app.api.v1.ai.generate_section_text_stub", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = ("Generated text", "test-model")
        
        # Mock the prompt builder to capture the language parameter
        with patch("app.api.v1.ai.build_generate_section_prompt") as mock_prompt_builder:
            mock_prompt_builder.return_value = "Test prompt"
            
            response = client.post(
                "/api/v1/ai/generate-section-text",
                json={
                    "study_id": test_study.id,
                    "section_id": test_section_ru.id,
                },
                headers=headers,
            )
            
            assert response.status_code == 200
            
            # Verify that prompt builder was called with language="ru" (document language)
            # not "en" (user UI language or request language)
            call_kwargs = mock_prompt_builder.call_args[1]
            assert call_kwargs.get("language") == "ru"


def test_ai_prompt_contains_language_specific_instructions():
    """Test that generated prompts contain language-specific instructions."""
    study = MagicMock(spec=Study)
    study.title = "Test Study"
    study.code = "TEST-001"
    study.phase = None
    study.indication = None
    study.sponsor_name = None
    
    section = MagicMock(spec=OutputSection)
    section.title = "Synopsis"
    section.code = "SYNOPSIS"
    
    # Test English prompt
    prompt_en = build_generate_section_prompt(
        study=study,
        section=section,
        current_text=None,
        rag_context_by_source_type={},
        user_prompt=None,
        language="en",
    )
    
    # Test Russian prompt
    prompt_ru = build_generate_section_prompt(
        study=study,
        section=section,
        current_text=None,
        rag_context_by_source_type={},
        user_prompt=None,
        language="ru",
    )
    
    # Prompts should be different
    assert prompt_en != prompt_ru
    
    # English prompt should contain English instructions
    assert "Write in English, using medical terminology" in prompt_en
    assert "You are an expert" in prompt_en
    
    # Russian prompt should contain Russian instructions
    assert "Пиши на русском языке, используя медицинскую терминологию" in prompt_ru
    assert "Ты — эксперт" in prompt_ru

