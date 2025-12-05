from pydantic import BaseModel, ConfigDict
from datetime import datetime


class RagChunkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    study_id: int
    source_document_id: int | None = None
    source_type: str
    order_index: int
    text: str
    created_at: datetime


class RagStudyChunksResponse(BaseModel):
    study_id: int
    source_type: str | None = None
    total_chunks: int
    limit: int
    offset: int
    chunks: list[RagChunkRead]

