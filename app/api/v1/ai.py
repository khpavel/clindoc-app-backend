from fastapi import APIRouter

from app.schemas.ai import GenerateSectionTextRequest, GenerateSectionTextResponse

router = APIRouter()


@router.post("/ai/generate-section-text", response_model=GenerateSectionTextResponse)
def generate_section_text(request: GenerateSectionTextRequest):
    """
    Generate text for a section using AI.
    
    This is a stub implementation that will later be replaced with a real LLM call.
    """
    return GenerateSectionTextResponse(
        section_id=request.section_id,
        generated_text=f"This is a stub text for section {request.section_id}",
        model="stub",
    )

