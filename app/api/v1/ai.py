from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.csr import CsrSection, CsrDocument, CsrSectionVersion
from app.models.study import Study
from app.models.ai import AiCallLog
from app.models.template import Template
from app.schemas.ai import GenerateSectionTextRequest, GenerateSectionTextResponse
from app.services.ai_client import generate_section_text_stub, generate_section_text_real
from app.services.rag_retrieval import retrieve_rag_chunks, build_rag_context_text
from app.services.template_context import build_template_context
from app.services.template_renderer import render_template_content
from app.services.ai_prompt_builder import build_generate_section_prompt
from app.core.config import settings
from sqlalchemy import desc

from app.deps.auth import get_current_active_user
from app.deps.study_access import verify_study_access
from app.models.user import User

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/generate-section-text", response_model=GenerateSectionTextResponse)
async def generate_section_text(
    body: GenerateSectionTextRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Generate CSR section text using AI.
    
    Validates that the section belongs to the study's CSR document,
    calls the AI service, logs the call, and returns the generated text.
    """
    # Verify user has access to the study
    study = verify_study_access(body.study_id, current_user.id, db)
    
    # Validate that CsrSection with body.section_id exists
    section = db.query(CsrSection).filter(CsrSection.id == body.section_id).first()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found"
        )
    
    # Validate that the section belongs to CSR document of body.study_id
    document = db.query(CsrDocument).filter(CsrDocument.id == section.document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CSR document not found for this section"
        )
    
    if document.study_id != body.study_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Section does not belong to study"
        )
    
    # Get current section text (latest version if exists)
    current_text = None
    latest_version = (
        db.query(CsrSectionVersion)
        .filter(CsrSectionVersion.section_id == section.id)
        .order_by(desc(CsrSectionVersion.created_at), desc(CsrSectionVersion.id))
        .first()
    )
    if latest_version:
        current_text = latest_version.text
    
    # Retrieve RAG chunks and build context
    chunks_by_type = retrieve_rag_chunks(db, study_id=body.study_id)
    rag_context_by_source_type = build_rag_context_text(chunks_by_type)
    
    # Get prompt template for this section
    # Try to find a prompt template by section_code, type="prompt", language="ru", is_active=True
    prompt_template = (
        db.query(Template)
        .filter(
            Template.type == "prompt",
            Template.section_code == section.code,
            Template.language == "ru",
            Template.is_active == True,
        )
        .order_by(Template.is_default.desc(), Template.version.desc())
        .first()
    )
    
    # Build effective prompt string
    if prompt_template:
        # Build base template context with study info
        base_context = build_template_context(db, body.study_id)
        # Map context dict keys to template variable names
        # e.g., "protocol" -> "context_protocol", "sap" -> "context_sap", etc.
        template_context_vars = {
            "context_protocol": rag_context_by_source_type.get("protocol", ""),
            "context_sap": rag_context_by_source_type.get("sap", ""),
            "context_tlf_summary": rag_context_by_source_type.get("tlf", ""),
            "context_csr_prev": rag_context_by_source_type.get("csr_prev", ""),
        }
        # Merge with RAG context variables
        full_context = {**base_context, **template_context_vars}
        # Render the template
        rendered_prompt, _, _ = render_template_content(prompt_template, full_context)
        effective_prompt = rendered_prompt
    else:
        # Use prompt builder to construct the prompt
        effective_prompt = build_generate_section_prompt(
            study=study,
            section=section,
            current_text=current_text,
            rag_context_by_source_type=rag_context_by_source_type,
            user_prompt=body.prompt,
        )
    
    try:
        # Choose implementation based on AI_MODE setting
        ai_mode = settings.ai_mode.lower()
        if ai_mode == "real":
            generate_func = generate_section_text_real
            mode = "real"
        else:
            generate_func = generate_section_text_stub
            mode = "stub"
        
        # Call the selected function to get (generated_text, model_name)
        generated_text, model_name = await generate_func(
            study_id=body.study_id,
            section_id=body.section_id,
            prompt=effective_prompt,
            max_tokens=body.max_tokens,
            temperature=body.temperature,
        )
        
        # Create an AiCallLog record with success=True, including mode
        ai_log = AiCallLog(
            study_id=body.study_id,
            section_id=body.section_id,
            prompt=effective_prompt,
            generated_text=generated_text,
            model_name=model_name,
            mode=mode,
            success=True,
        )
        db.add(ai_log)
        db.commit()
        
        # Return GenerateSectionTextResponse
        return GenerateSectionTextResponse(
            study_id=body.study_id,
            section_id=body.section_id,
            generated_text=generated_text,
            model_name=model_name,
            created_at=datetime.utcnow(),
        )
        
    except Exception as e:
        # In case of unexpected errors, catch them, log an AiCallLog with success=False
        error_message = str(e)
        ai_mode = settings.ai_mode.lower()
        mode = "real" if ai_mode == "real" else "stub"
        ai_log = AiCallLog(
            study_id=body.study_id,
            section_id=body.section_id,
            prompt=effective_prompt,
            generated_text=None,
            model_name=None,
            mode=mode,
            success=False,
            error_message=error_message,
        )
        db.add(ai_log)
        db.commit()
        
        # Raise HTTPException(500, "AI generation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI generation failed"
        )
