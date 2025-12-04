from pydantic import BaseModel
from datetime import datetime


class TemplateBase(BaseModel):
    name: str
    description: str | None = None
    type: str
    section_code: str | None = None
    language: str = "en"
    scope: str = "global"
    is_default: bool = False
    is_active: bool = True


class TemplateRead(TemplateBase):
    id: int
    version: int
    content: str
    variables: dict | None = None
    created_at: datetime
    updated_at: datetime
    created_by: str | None = None

    class Config:
        orm_mode = True


class TemplateRenderRequest(BaseModel):
    study_id: int
    section_id: int | None = None
    extra_context: dict | None = None


class TemplateRenderResponse(BaseModel):
    rendered_text: str
    used_variables: dict[str, str] | None = None
    missing_variables: list[str] | None = None

