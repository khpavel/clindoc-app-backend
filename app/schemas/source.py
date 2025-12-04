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

    class Config:
        orm_mode = True


class SourceDocumentCreate(BaseModel):
    study_id: int
    type: str
    file_name: str
    uploaded_by: str | None = None
