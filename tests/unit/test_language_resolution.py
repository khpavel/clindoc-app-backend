"""
Unit tests for language resolution functionality.

Tests:
1. get_request_language - with user preference, without user, default fallback
2. resolve_content_language - document language, user preference, request language precedence
"""
import pytest
from unittest.mock import Mock, MagicMock
from fastapi import Request

from app.deps.language import get_request_language
from app.services.language_resolver import resolve_content_language
from app.models.user import User
from app.models.document import Document


class TestGetRequestLanguage:
    """Tests for get_request_language dependency."""
    
    def test_user_ui_language_preferred_over_accept_language(self):
        """Test that user.ui_language takes precedence over Accept-Language header."""
        # Create a mock user with ui_language="ru"
        user = Mock(spec=User)
        user.ui_language = "ru"
        
        # Create a mock request with Accept-Language="en-US"
        request = Mock(spec=Request)
        request.headers = {"Accept-Language": "en-US"}
        
        # Call get_request_language
        result = get_request_language(request=request, user=user)
        
        # Should return "ru" (user preference), not "en" (header)
        assert result == "ru"
    
    def test_without_user_falls_back_to_accept_language_en(self):
        """Test that without user, Accept-Language header is used."""
        # No user
        user = None
        
        # Create a mock request with Accept-Language="en-US"
        request = Mock(spec=Request)
        request.headers = {"Accept-Language": "en-US"}
        
        # Call get_request_language
        result = get_request_language(request=request, user=user)
        
        # Should return "en" from header
        assert result == "en"
    
    def test_without_user_and_header_falls_back_to_default(self):
        """Test that without user and without header, defaults to 'en'."""
        # No user
        user = None
        
        # Create a mock request without Accept-Language header
        request = Mock(spec=Request)
        request.headers = {}
        
        # Call get_request_language
        result = get_request_language(request=request, user=user)
        
        # Should return default "en"
        assert result == "en"
    
    def test_user_ui_language_none_falls_back_to_header(self):
        """Test that if user.ui_language is None, falls back to header."""
        # User with no ui_language set
        user = Mock(spec=User)
        user.ui_language = None
        
        # Create a mock request with Accept-Language="ru"
        request = Mock(spec=Request)
        request.headers = {"Accept-Language": "ru"}
        
        # Call get_request_language
        result = get_request_language(request=request, user=user)
        
        # Should return "ru" from header
        assert result == "ru"
    
    def test_accept_language_with_ru(self):
        """Test Accept-Language header parsing with 'ru'."""
        user = None
        request = Mock(spec=Request)
        request.headers = {"Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8"}
        
        result = get_request_language(request=request, user=user)
        assert result == "ru"
    
    def test_accept_language_with_en(self):
        """Test Accept-Language header parsing with 'en'."""
        user = None
        request = Mock(spec=Request)
        request.headers = {"Accept-Language": "en-US,en;q=0.9"}
        
        result = get_request_language(request=request, user=user)
        assert result == "en"


class TestResolveContentLanguage:
    """Tests for resolve_content_language function."""
    
    def test_document_language_takes_precedence(self):
        """Test that document.language takes precedence over user and request language."""
        # Document with language="en"
        document = Mock(spec=Document)
        document.language = "en"
        
        # User with ui_language="ru"
        user = Mock(spec=User)
        user.ui_language = "ru"
        
        # Request language="ru"
        request_language = "ru"
        
        # Call resolve_content_language
        result = resolve_content_language(document, user, request_language)
        
        # Should return "en" (document language), not "ru"
        assert result == "en"
    
    def test_no_document_falls_back_to_user_ui_language(self):
        """Test that without document, user.ui_language is used."""
        # No document
        document = None
        
        # User with ui_language="ru"
        user = Mock(spec=User)
        user.ui_language = "ru"
        
        # Request language="en"
        request_language = "en"
        
        # Call resolve_content_language
        result = resolve_content_language(document, user, request_language)
        
        # Should return "ru" (user preference)
        assert result == "ru"
    
    def test_no_document_no_user_falls_back_to_request_language(self):
        """Test that without document and user, request_language is used."""
        # No document
        document = None
        
        # No user
        user = None
        
        # Request language="en"
        request_language = "en"
        
        # Call resolve_content_language
        result = resolve_content_language(document, user, request_language)
        
        # Should return "en" (request language)
        assert result == "en"
    
    def test_document_language_none_falls_back_to_user(self):
        """Test that if document.language is None, falls back to user.ui_language."""
        # Document with language=None
        document = Mock(spec=Document)
        document.language = None
        
        # User with ui_language="ru"
        user = Mock(spec=User)
        user.ui_language = "ru"
        
        # Request language="en"
        request_language = "en"
        
        # Call resolve_content_language
        result = resolve_content_language(document, user, request_language)
        
        # Should return "ru" (user preference)
        assert result == "ru"
    
    def test_document_language_invalid_falls_back_to_user(self):
        """Test that if document.language is invalid, falls back to user.ui_language."""
        # Document with invalid language
        document = Mock(spec=Document)
        document.language = "fr"  # Invalid, should be "ru" or "en"
        
        # User with ui_language="ru"
        user = Mock(spec=User)
        user.ui_language = "ru"
        
        # Request language="en"
        request_language = "en"
        
        # Call resolve_content_language
        result = resolve_content_language(document, user, request_language)
        
        # Should return "ru" (user preference)
        assert result == "ru"
    
    def test_user_ui_language_none_falls_back_to_request(self):
        """Test that if user.ui_language is None, falls back to request_language."""
        # Document with language=None
        document = Mock(spec=Document)
        document.language = None
        
        # User with ui_language=None
        user = Mock(spec=User)
        user.ui_language = None
        
        # Request language="en"
        request_language = "en"
        
        # Call resolve_content_language
        result = resolve_content_language(document, user, request_language)
        
        # Should return "en" (request language)
        assert result == "en"
    
    def test_all_none_falls_back_to_default(self):
        """Test that if all are None/invalid, falls back to default 'en'."""
        # Document with language=None
        document = Mock(spec=Document)
        document.language = None
        
        # No user
        user = None
        
        # Invalid request language
        request_language = "fr"  # Invalid
        
        # Call resolve_content_language
        result = resolve_content_language(document, user, request_language)
        
        # Should return "en" (default fallback)
        assert result == "en"

