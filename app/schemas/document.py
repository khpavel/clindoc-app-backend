from datetime import datetime

from pydantic import BaseModel, field_validator


# Allowed document types
ALLOWED_DOCUMENT_TYPES = {"csr", "protocol", "ib", "sap", "tlf"}

# Allowed document statuses
ALLOWED_DOCUMENT_STATUSES = {"draft", "in_qc", "ready_for_submission", "archived"}


class DocumentBase(BaseModel):
    type: str
    title: str
    template_code: str | None = None
    status: str = "draft"
    current_version_label: str | None = None
    # Content language of the document ("ru" or "en")
    language: str = "ru"
    
    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v not in ALLOWED_DOCUMENT_TYPES:
            allowed = ", ".join(sorted(ALLOWED_DOCUMENT_TYPES))
            raise ValueError(f"Document type must be one of: {allowed}")
        return v
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v not in ALLOWED_DOCUMENT_STATUSES:
            allowed = ", ".join(sorted(ALLOWED_DOCUMENT_STATUSES))
            raise ValueError(f"Document status must be one of: {allowed}")
        return v


class DocumentCreate(BaseModel):
    type: str
    title: str
    template_code: str | None = None
    status: str = "draft"
    current_version_label: str | None = None
    # Content language of the document ("ru" or "en")
    language: str = "ru"
    
    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v not in ALLOWED_DOCUMENT_TYPES:
            allowed = ", ".join(sorted(ALLOWED_DOCUMENT_TYPES))
            raise ValueError(f"Document type must be one of: {allowed}")
        return v
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v not in ALLOWED_DOCUMENT_STATUSES:
            allowed = ", ".join(sorted(ALLOWED_DOCUMENT_STATUSES))
            raise ValueError(f"Document status must be one of: {allowed}")
        return v


class DocumentRead(DocumentBase):
    id: int
    study_id: int
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

