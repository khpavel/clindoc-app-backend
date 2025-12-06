from pydantic import BaseModel

from app.models.study import StudyStatus


class StudyBase(BaseModel):
    code: str
    title: str
    phase: str | None = None
    status: StudyStatus = StudyStatus.DRAFT
    indication: str | None = None
    sponsor_name: str | None = None


class StudyCreate(StudyBase):
    pass


class StudyRead(StudyBase):
    id: int

    class Config:
        orm_mode = True
