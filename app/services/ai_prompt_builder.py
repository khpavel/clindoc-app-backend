"""
Service for building prompts for AI generation of CSR section text.
"""
from typing import Optional

from app.models.study import Study
from app.models.output_document import OutputSection


def build_generate_section_prompt(
    study: Study,
    section: OutputSection,
    current_text: Optional[str],
    rag_context_by_source_type: dict[str, str],
    user_prompt: Optional[str],
    language: str = "ru",
) -> str:
    """
    Build a complete prompt for AI generation of CSR section text.
    
    Args:
        study: Study object with study information
        section: OutputSection object with section information
        current_text: Current text of the section (if exists), None otherwise
        rag_context_by_source_type: Dictionary with RAG context by source type
            (e.g., {"protocol": "...", "sap": "...", "tlf": "...", "csr_prev": "..."})
        user_prompt: Optional user-provided prompt/instruction
        language: Language code ("ru" or "en") for the generated text
    
    Returns:
        Complete prompt string ready to be sent to AI/LLM
    """
    # Build system/instruction part
    if language == "ru":
        system_parts = [
            "Ты — эксперт по написанию разделов Clinical Study Report (CSR) для клинических исследований.",
            f"Ты работаешь над исследованием: {study.title} (код: {study.code}).",
            f"Тебе нужно сгенерировать или улучшить текст для раздела: {section.title} (код: {section.code}).",
            "",
            "Формат ответа:",
            "- Текст должен быть структурированным, профессиональным и соответствовать стандартам CSR.",
            "- Используй только информацию из предоставленного контекста.",
            "- Если в контексте недостаточно информации, укажи это в соответствующих местах.",
            "- Пиши на русском языке, используя медицинскую терминологию.",
        ]
    else:  # language == "en"
        system_parts = [
            "You are an expert in writing Clinical Study Report (CSR) sections for clinical trials.",
            f"You are working on the study: {study.title} (code: {study.code}).",
            f"You need to generate or improve text for the section: {section.title} (code: {section.code}).",
            "",
            "Response format:",
            "- The text should be structured, professional, and comply with CSR standards.",
            "- Use only information from the provided context.",
            "- If there is insufficient information in the context, indicate this in the appropriate places.",
            "- Write in English, using medical terminology.",
        ]
    
    # Add study-specific information if available
    if language == "ru":
        if study.phase:
            system_parts.append(f"- Фаза исследования: {study.phase}.")
        if study.indication:
            system_parts.append(f"- Показание к применению: {study.indication}.")
        if study.sponsor_name:
            system_parts.append(f"- Спонсор: {study.sponsor_name}.")
        
        system_parts.append("")
        system_parts.append("=== КОНТЕКСТ ИЗ ИСХОДНЫХ ДОКУМЕНТОВ ===")
        system_parts.append("")
        
        # Add structured context blocks separately for each source type
        protocol_context = rag_context_by_source_type.get("protocol", "")
        if protocol_context:
            system_parts.append("--- ПРОТОКОЛ ИССЛЕДОВАНИЯ ---")
            system_parts.append(protocol_context)
            system_parts.append("")
        
        sap_context = rag_context_by_source_type.get("sap", "")
        if sap_context:
            system_parts.append("--- SAP (Statistical Analysis Plan) ---")
            system_parts.append(sap_context)
            system_parts.append("")
        
        tlf_context = rag_context_by_source_type.get("tlf", "")
        if tlf_context:
            system_parts.append("--- TLF (Table, Listing, Figure) - Сводные данные ---")
            system_parts.append(tlf_context)
            system_parts.append("")
        
        csr_prev_context = rag_context_by_source_type.get("csr_prev", "")
        if csr_prev_context:
            system_parts.append("--- ПРЕДЫДУЩИЙ CSR ---")
            system_parts.append(csr_prev_context)
            system_parts.append("")
        
        # Add current section text if exists
        if current_text:
            system_parts.append("=== ТЕКУЩИЙ ТЕКСТ РАЗДЕЛА ===")
            system_parts.append("")
            system_parts.append(current_text)
            system_parts.append("")
        
        # Add user prompt if provided
        if user_prompt:
            system_parts.append("=== ДОПОЛНИТЕЛЬНЫЕ ИНСТРУКЦИИ ===")
            system_parts.append("")
            system_parts.append(user_prompt)
            system_parts.append("")
        else:
            # Default instruction if no user prompt
            system_parts.append("=== ЗАДАНИЕ ===")
            system_parts.append("")
            system_parts.append("Сгенерируй текст раздела CSR на основе приведённого контекста.")
            system_parts.append("")
    else:  # language == "en"
        if study.phase:
            system_parts.append(f"- Study phase: {study.phase}.")
        if study.indication:
            system_parts.append(f"- Indication: {study.indication}.")
        if study.sponsor_name:
            system_parts.append(f"- Sponsor: {study.sponsor_name}.")
        
        system_parts.append("")
        system_parts.append("=== CONTEXT FROM SOURCE DOCUMENTS ===")
        system_parts.append("")
        
        # Add structured context blocks separately for each source type
        protocol_context = rag_context_by_source_type.get("protocol", "")
        if protocol_context:
            system_parts.append("--- STUDY PROTOCOL ---")
            system_parts.append(protocol_context)
            system_parts.append("")
        
        sap_context = rag_context_by_source_type.get("sap", "")
        if sap_context:
            system_parts.append("--- SAP (Statistical Analysis Plan) ---")
            system_parts.append(sap_context)
            system_parts.append("")
        
        tlf_context = rag_context_by_source_type.get("tlf", "")
        if tlf_context:
            system_parts.append("--- TLF (Table, Listing, Figure) - Summary Data ---")
            system_parts.append(tlf_context)
            system_parts.append("")
        
        csr_prev_context = rag_context_by_source_type.get("csr_prev", "")
        if csr_prev_context:
            system_parts.append("--- PREVIOUS CSR ---")
            system_parts.append(csr_prev_context)
            system_parts.append("")
        
        # Add current section text if exists
        if current_text:
            system_parts.append("=== CURRENT SECTION TEXT ===")
            system_parts.append("")
            system_parts.append(current_text)
            system_parts.append("")
        
        # Add user prompt if provided
        if user_prompt:
            system_parts.append("=== ADDITIONAL INSTRUCTIONS ===")
            system_parts.append("")
            system_parts.append(user_prompt)
            system_parts.append("")
        else:
            # Default instruction if no user prompt
            system_parts.append("=== TASK ===")
            system_parts.append("")
            system_parts.append("Generate CSR section text based on the provided context.")
            system_parts.append("")
    
    return "\n".join(system_parts)

