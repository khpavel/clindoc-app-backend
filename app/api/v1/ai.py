from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.csr import CsrSection, CsrDocument
from app.models.study import Study
from app.models.ai import AiCallLog
from app.schemas.ai import GenerateSectionTextRequest, GenerateSectionTextResponse
from app.services.ai_client import generate_section_text_stub

# Optional: Import get_current_active_user if available for future use
try:
    from app.deps.auth import get_current_active_user
    from app.models.user import User
except ImportError:
    get_current_active_user = None
    User = None

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/generate-section-text", response_model=GenerateSectionTextResponse)
async def generate_section_text(
    body: GenerateSectionTextRequest,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_active_user)  # if available
):
    """
    Generate CSR section text using AI.
    
    Validates that the section belongs to the study's CSR document,
    calls the AI service, logs the call, and returns the generated text.
    """
    # Validate that study exists
    study = db.query(Study).filter(Study.id == body.study_id).first()
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found"
        )
    
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
    
    # Build effective prompt string
    effective_prompt = body.prompt or "Generate CSR text for this section."
    
    try:
        # Call generate_section_text_stub to get (generated_text, model_name)
        generated_text, model_name = await generate_section_text_stub(
            study_id=body.study_id,
            section_id=body.section_id,
            prompt=effective_prompt,
            max_tokens=body.max_tokens,
            temperature=body.temperature,
        )
        
        # Create an AiCallLog record with success=True
        ai_log = AiCallLog(
            study_id=body.study_id,
            section_id=body.section_id,
            prompt=effective_prompt,
            generated_text=generated_text,
            model_name=model_name,
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
        ai_log = AiCallLog(
            study_id=body.study_id,
            section_id=body.section_id,
            prompt=effective_prompt,
            generated_text=None,
            model_name=None,
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
