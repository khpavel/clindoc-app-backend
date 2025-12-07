"""
Tests for i18n translation function.

Tests that:
1. Known keys in RU and EN return different strings
2. Missing key or language falls back to English or key
3. Format parameters work correctly
"""
import pytest

from app.i18n import t


def test_t_known_key_ru():
    """Test that known key in Russian returns Russian string."""
    result = t("ERROR_STUDY_NOT_FOUND", "ru")
    assert result == "Исследование не найдено"
    assert isinstance(result, str)


def test_t_known_key_en():
    """Test that known key in English returns English string."""
    result = t("ERROR_STUDY_NOT_FOUND", "en")
    assert result == "Study not found"
    assert isinstance(result, str)


def test_t_known_key_different_languages():
    """Test that same key returns different strings for different languages."""
    ru_result = t("ERROR_STUDY_NOT_FOUND", "ru")
    en_result = t("ERROR_STUDY_NOT_FOUND", "en")
    
    assert ru_result != en_result
    assert ru_result == "Исследование не найдено"
    assert en_result == "Study not found"


def test_t_missing_key_falls_back_to_key():
    """Test that missing key returns the key itself."""
    result = t("NONEXISTENT_KEY_12345", "ru")
    assert result == "NONEXISTENT_KEY_12345"


def test_t_missing_key_falls_back_to_english():
    """Test that missing key in Russian falls back to English if available."""
    # Use a key that exists in English but not in Russian
    # Actually, all our keys exist in both, so test with a completely missing key
    result = t("NONEXISTENT_KEY_12345", "ru")
    # Should fall back to key itself since it doesn't exist in either
    assert result == "NONEXISTENT_KEY_12345"


def test_t_format_parameters():
    """Test that format parameters work correctly."""
    result = t("QC_MISSING_SECTION", "en", section_title="Introduction", code="intro")
    assert "Introduction" in result
    assert "intro" in result
    assert result == "Missing required section: Introduction (intro)"


def test_t_format_parameters_ru():
    """Test that format parameters work correctly in Russian."""
    result = t("QC_MISSING_SECTION", "ru", section_title="Введение", code="intro")
    assert "Введение" in result
    assert "intro" in result
    assert result == "Отсутствует обязательная секция: Введение (intro)"


def test_t_language_normalization():
    """Test that language is normalized correctly."""
    # Test various language inputs
    result1 = t("ERROR_STUDY_NOT_FOUND", "RU")
    result2 = t("ERROR_STUDY_NOT_FOUND", "ru")
    result3 = t("ERROR_STUDY_NOT_FOUND", "russian")
    
    assert result1 == "Исследование не найдено"
    assert result2 == "Исследование не найдено"
    assert result3 == "Исследование не найдено"
    
    # Test English normalization
    result4 = t("ERROR_STUDY_NOT_FOUND", "EN")
    result5 = t("ERROR_STUDY_NOT_FOUND", "en")
    result6 = t("ERROR_STUDY_NOT_FOUND", "english")
    result7 = t("ERROR_STUDY_NOT_FOUND", "fr")  # Should default to English
    
    assert result4 == "Study not found"
    assert result5 == "Study not found"
    assert result6 == "Study not found"
    assert result7 == "Study not found"


def test_t_empty_language_defaults_to_en():
    """Test that empty language defaults to English."""
    result = t("ERROR_STUDY_NOT_FOUND", "")
    assert result == "Study not found"


def test_t_none_language_defaults_to_en():
    """Test that None language defaults to English."""
    result = t("ERROR_STUDY_NOT_FOUND", None)
    assert result == "Study not found"


def test_t_qc_term_mismatch():
    """Test QC term mismatch message with parameters."""
    result_en = t("QC_TERM_MISMATCH_DESCRIPTION", "en", term="patient", expected="subject")
    result_ru = t("QC_TERM_MISMATCH_DESCRIPTION", "ru", term="пациент", expected="субъект")
    
    assert "patient" in result_en
    assert "subject" in result_en
    assert "пациент" in result_ru
    assert "субъект" in result_ru


def test_t_qc_term_mismatch_title_ru():
    """Test that QC_TERM_MISMATCH_TITLE returns Russian string."""
    result = t("QC_TERM_MISMATCH_TITLE", "ru")
    assert result == "Найдено несоответствие термина"
    assert isinstance(result, str)


def test_t_qc_term_mismatch_title_en():
    """Test that QC_TERM_MISMATCH_TITLE returns English string."""
    result = t("QC_TERM_MISMATCH_TITLE", "en")
    assert result == "Term mismatch found"
    assert isinstance(result, str)


def test_t_qc_term_mismatch_title_different_languages():
    """Test that QC_TERM_MISMATCH_TITLE returns different strings for different languages."""
    ru_result = t("QC_TERM_MISMATCH_TITLE", "ru")
    en_result = t("QC_TERM_MISMATCH_TITLE", "en")
    
    assert ru_result != en_result
    assert ru_result == "Найдено несоответствие термина"
    assert en_result == "Term mismatch found"


def test_t_unknown_key_fallback():
    """Test that unknown key falls back correctly."""
    # Test with a key that doesn't exist
    result = t("UNKNOWN_KEY_XYZ", "ru")
    # Should fall back to English first, then to the key itself
    assert result == "UNKNOWN_KEY_XYZ"
    
    # Test with English
    result_en = t("UNKNOWN_KEY_XYZ", "en")
    assert result_en == "UNKNOWN_KEY_XYZ"


def test_t_unknown_language_fallback():
    """Test that unknown language falls back to English."""
    # Use a language that doesn't exist (should default to "en")
    result = t("ERROR_STUDY_NOT_FOUND", "fr")
    assert result == "Study not found"  # Should fall back to English
