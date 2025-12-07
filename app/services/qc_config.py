"""
QC configuration with per-language support.

This module provides language-specific configuration for QC rules,
allowing different rule parameters or reference term lists per language.
"""
from typing import Dict, Any


# QC configuration organized by language
# Each language can have different rule parameters, term dictionaries, etc.
QC_CONFIG: Dict[str, Dict[str, Any]] = {
    "ru": {
        # Russian-language QC configuration
        "required_sections": {
            "enabled": True,
            "severity": "warning",
        },
        # Example: term dictionaries for Russian QC rules
        "term_dictionaries": {
            # Placeholder for future language-specific term lists
            # "medical_terms": [...],
            # "regulatory_terms": [...],
        },
    },
    "en": {
        # English-language QC configuration
        "required_sections": {
            "enabled": True,
            "severity": "warning",
        },
        # Example: term dictionaries for English QC rules
        "term_dictionaries": {
            # Placeholder for future language-specific term lists
            # "medical_terms": [...],
            # "regulatory_terms": [...],
        },
    },
}


def get_qc_config_for_language(language: str) -> Dict[str, Any]:
    """
    Get QC configuration for a specific language.
    
    Args:
        language: Language code ("ru" or "en")
    
    Returns:
        Dictionary with QC configuration for the language.
        Falls back to "en" if language is not found.
    """
    if language not in ("ru", "en"):
        language = "en"
    
    return QC_CONFIG.get(language, QC_CONFIG["en"])


def get_qc_rule_config(rule_code: str, language: str) -> Dict[str, Any]:
    """
    Get configuration for a specific QC rule in a specific language.
    
    Args:
        rule_code: Code of the QC rule (e.g., "REQUIRED_SECTIONS")
        language: Language code ("ru" or "en")
    
    Returns:
        Dictionary with rule configuration, or empty dict if not found.
    """
    config = get_qc_config_for_language(language)
    
    # Map rule codes to configuration keys
    rule_key_mapping = {
        "REQUIRED_SECTIONS": "required_sections",
    }
    
    config_key = rule_key_mapping.get(rule_code)
    if config_key:
        return config.get(config_key, {})
    
    return {}

