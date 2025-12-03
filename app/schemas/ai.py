from pydantic import BaseModel


class GenerateSectionTextRequest(BaseModel):
    section_id: int
    prompt: str


class GenerateSectionTextResponse(BaseModel):
    section_id: int
    generated_text: str
    model: str

