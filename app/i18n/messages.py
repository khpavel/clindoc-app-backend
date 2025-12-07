"""Message dictionaries and translation helper for i18n."""

from typing import Any

# Message dictionaries for Russian and English
MESSAGES = {
    "ru": {
        # QC messages
        "QC_MISSING_SECTION": "Отсутствует обязательная секция: {section_title} ({code})",
        "QC_TERM_MISMATCH_TITLE": "Найдено несоответствие термина",
        "QC_TERM_MISMATCH_DESCRIPTION": "Термин '{term}' не соответствует ожидаемому '{expected}'",
        
        # Error messages
        "ERROR_STUDY_NOT_FOUND": "Исследование не найдено",
        "ERROR_ACCESS_DENIED_NOT_MEMBER": "Доступ запрещён: вы не являетесь участником этого исследования",
        "ERROR_ACCESS_DENIED_MANAGEMENT": "Доступ запрещён: только владельцы исследования могут управлять участниками",
        "ERROR_ACCESS_DENIED_EDITOR": "Доступ запрещён: только владельцы и редакторы исследования могут выполнять это действие",
    },
    "en": {
        # QC messages
        "QC_MISSING_SECTION": "Missing required section: {section_title} ({code})",
        "QC_TERM_MISMATCH_TITLE": "Term mismatch found",
        "QC_TERM_MISMATCH_DESCRIPTION": "Term '{term}' does not match expected '{expected}'",
        
        # Error messages
        "ERROR_STUDY_NOT_FOUND": "Study not found",
        "ERROR_ACCESS_DENIED_NOT_MEMBER": "Access denied: You are not a member of this study",
        "ERROR_ACCESS_DENIED_MANAGEMENT": "Access denied: Only study owners can manage members",
        "ERROR_ACCESS_DENIED_EDITOR": "Access denied: Only study owners and editors can perform this action",
    },
}


def t(key: str, language: str = "en", **kwargs: Any) -> str:
    """
    Translate a message key to the specified language.
    
    Args:
        key: Message key to translate
        language: Language code ("ru" or "en"). Will be normalized to "ru" or "en".
        **kwargs: Format parameters for the message template
    
    Returns:
        Translated message string. Falls back to:
        1. English version if language not found
        2. The key itself if no entry exists
    """
    # Normalize language to "ru" or "en"
    normalized_lang = "ru" if language and language.lower().startswith("ru") else "en"
    
    # Try to get message from the requested language
    messages = MESSAGES.get(normalized_lang, {})
    message = messages.get(key)
    
    # Fallback to English if not found in requested language
    if message is None and normalized_lang != "en":
        messages_en = MESSAGES.get("en", {})
        message = messages_en.get(key)
    
    # Fallback to key itself if no entry exists
    if message is None:
        message = key
    
    # Format the message if kwargs are provided
    if kwargs:
        try:
            return message.format(**kwargs)
        except (KeyError, ValueError):
            # If formatting fails, return the message as-is
            return message
    
    return message

