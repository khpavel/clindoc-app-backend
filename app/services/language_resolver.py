"""
Service for resolving content language based on document, user, and request context.

Content language is distinct from UI/request language:
- UI/request language: Used for interface elements, error messages, etc.
- Content language: Used for document content generation (AI, QC, templates, RAG)

This module provides functions to determine the appropriate content language
when generating or processing document content.
"""
from typing import Optional

from app.models.document import Document
from app.models.user import User


def resolve_content_language(
    document: Optional[Document],
    user: Optional[User],
    request_language: str,
) -> str:
    """
    Resolve the content language for document processing.
    
    This function determines which language should be used when generating or processing
    document content (AI generation, QC checks, template rendering, RAG retrieval).
    The content language is separate from the UI language - a user with Russian UI
    can work on an English document.
    
    Precedence (in order):
    1. document.language - if document exists and has a valid language set
    2. user.ui_language - if user exists and has a ui_language preference
    3. request_language - fallback to the request-level language
    
    Args:
        document: Optional Document object. If provided and document.language is set
                  and valid ("ru" or "en"), it takes precedence.
        user: Optional User object. If provided and user.ui_language is set and valid,
              it is used as fallback if document language is not available.
        request_language: Request-level language (from Accept-Language header or default).
                          Used as final fallback. Should already be validated to be "ru" or "en".
    
    Returns:
        Language code: "ru" or "en"
    
    Examples:
        # Document with language set
        doc = Document(language="en", ...)
        resolve_content_language(doc, user, "ru")  # Returns "en"
        
        # No document, user with Russian UI
        user = User(ui_language="ru", ...)
        resolve_content_language(None, user, "en")  # Returns "ru"
        
        # No document, no user preference
        resolve_content_language(None, None, "ru")  # Returns "ru"
    """
    # Priority 1: Document's content language
    if document is not None and document.language:
        if document.language in ("ru", "en"):
            return document.language
    
    # Priority 2: User's UI language preference
    if user is not None and user.ui_language:
        if user.ui_language in ("ru", "en"):
            return user.ui_language
    
    # Priority 3: Request language (already validated by get_request_language)
    # Ensure it's valid, but it should already be "ru" or "en"
    if request_language in ("ru", "en"):
        return request_language
    
    # Final fallback (should rarely happen if request_language is properly validated)
    return "en"

