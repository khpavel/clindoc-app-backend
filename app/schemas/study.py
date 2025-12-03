from pydantic import BaseModel


class StudyBase(BaseModel):
    code: str
    title: str
    phase: str | None = None


class StudyCreate(StudyBase):
    pass


class StudyRead(StudyBase):
    id: int

    class Config:
        orm_mode = True
