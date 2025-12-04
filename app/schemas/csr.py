from datetime import datetime

from pydantic import BaseModel


class CsrSectionBase(BaseModel):
    code: str
    title: str
    order_index: int


class CsrSectionRead(CsrSectionBase):
    id: int

    class Config:
        orm_mode = True


class CsrSectionVersionBase(BaseModel):
    text: str


class CsrSectionVersionCreate(BaseModel):
    text: str
    created_by: str | None = None


class CsrSectionVersionRead(CsrSectionVersionBase):
    id: int
    created_at: datetime
    created_by: str | None = None
    source: str | None = None
    template_id: int | None = None

    class Config:
        orm_mode = True


class ApplyTemplateRequest(BaseModel):
    study_id: int
    template_id: int
    extra_context: dict | None = None


class CsrDocumentRead(BaseModel):
    id: int
    study_id: int
    title: str
    status: str
    sections: list[CsrSectionRead] = []

    class Config:
        orm_mode = True
