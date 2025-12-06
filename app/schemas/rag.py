from pydantic import BaseModel, ConfigDict
from datetime import datetime


class RagChunkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    study_id: int
    source_document_id: int | None = None
    source_type: str
    order_index: int
    text: str  # Full text
    text_preview: str  # Truncated text for list view (first 200 characters)
    created_at: datetime
    source_document_file_name: str | None = None  # File name of the source document for convenience


class RagStudyChunksResponse(BaseModel):
    study_id: int
    source_type: str | None = None
    total_chunks: int
    limit: int
    offset: int
    chunks: list[RagChunkRead]

