from pydantic import BaseModel


class SourceDocumentRead(BaseModel):
    id: int
    type: str
    file_name: str

    class Config:
        orm_mode = True

