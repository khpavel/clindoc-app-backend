from datetime import datetime

from pydantic import BaseModel


class SourceDocumentBase(BaseModel):
    id: int
    study_id: int
    type: str
    file_name: str
    uploaded_at: datetime


class SourceDocumentRead(SourceDocumentBase):
    uploaded_by: str | None = None
    language: str
    version_label: str | None = None
    status: str
    is_current: bool
    is_rag_enabled: bool
    index_status: str

    class Config:
        orm_mode = True


class SourceDocumentCreate(BaseModel):
    study_id: int
    type: str
    file_name: str
    uploaded_by: str | None = None
    language: str = "ru"
    version_label: str | None = None
    status: str = "active"
    is_rag_enabled: bool = True
