"""
Minimal contract for the AI assistant MVP - Pydantic schemas for AI section text generation.
"""
from datetime import datetime

from pydantic import BaseModel


class GenerateSectionTextRequest(BaseModel):
    study_id: int
    section_id: int
    prompt: str | None = None
    max_tokens: int | None = 1024
    temperature: float | None = 0.2


class GenerateSectionTextResponse(BaseModel):
    study_id: int
    section_id: int
    generated_text: str
    model_name: str | None = None
    created_at: datetime
