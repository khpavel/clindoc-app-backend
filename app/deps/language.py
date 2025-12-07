"""
Language dependency for request-level language context.

Determines the preferred UI language from:
1. User's ui_language preference (if authenticated)
2. Accept-Language header
3. Default fallback ("en")
"""
from typing import Optional

from fastapi import Depends, Request
from app.deps.auth import optional_current_user
from app.models.user import User


def get_request_language(
    request: Request,
    user: Optional[User] = Depends(optional_current_user),
) -> str:
    """
    Get the request language preference.
    
    Priority:
    1. If user is authenticated and user.ui_language is in {"ru", "en"} → return that
    2. Else parse Accept-Language header:
       - If it contains "ru" → "ru"
       - Else if it contains "en" → "en"
       - Else fallback to default ("en")
    
    Always returns "ru" or "en".
    """
    # Default language
    default_language = "en"
    
    # Check user preference first
    if user and user.ui_language and user.ui_language in {"ru", "en"}:
        return user.ui_language
    
    # Parse Accept-Language header
    if request:
        accept_language = request.headers.get("Accept-Language", "")
        accept_language_lower = accept_language.lower()
        
        # Check for "ru" first (more specific)
        if "ru" in accept_language_lower:
            return "ru"
        elif "en" in accept_language_lower:
            return "en"
    
    # Fallback to default
    return default_language

