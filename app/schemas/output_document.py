from datetime import datetime
from typing import Any

from pydantic import BaseModel


class OutputSectionBase(BaseModel):
    code: str
    title: str
    order_index: int


class OutputSectionRead(OutputSectionBase):
    id: int

    class Config:
        orm_mode = True


class OutputSectionVersionBase(BaseModel):
    text: str


class OutputSectionVersionCreate(BaseModel):
    text: str
    created_by: str | None = None


class OutputSectionVersionRead(OutputSectionVersionBase):
    id: int
    created_at: datetime
    created_by: str | None = None
    source: str | None = None
    template_id: int | None = None

    class Config:
        orm_mode = True


class ApplyTemplateRequest(BaseModel):
    template_id: int
    study_id: int
    extra_context: dict[str, Any] | None = None


class OutputDocumentRead(BaseModel):
    id: int
    study_id: int
    title: str
    status: str
    # Content language of the document ("ru" or "en")
    language: str = "ru"
    sections: list[OutputSectionRead] = []

    class Config:
        orm_mode = True


# ============================================================================
# Backward-Compatible Aliases for Deprecated /csr Endpoints
# ============================================================================
# These aliases maintain backward compatibility for deprecated /api/v1/csr/*
# endpoints. New code should use Output* names.
# ============================================================================

CsrSectionBase = OutputSectionBase
CsrSectionRead = OutputSectionRead
CsrSectionVersionBase = OutputSectionVersionBase
CsrSectionVersionCreate = OutputSectionVersionCreate
CsrSectionVersionRead = OutputSectionVersionRead
CsrDocumentRead = OutputDocumentRead


# Re-export aliases for convenience
CreateOutputSectionVersionRequest = OutputSectionVersionCreate
ApplyTemplateToSectionRequest = ApplyTemplateRequest

__all__ = [
    "OutputDocumentRead",
    "OutputSectionRead",
    "OutputSectionVersionRead",
    "OutputSectionVersionCreate",
    "ApplyTemplateRequest",
    "CreateOutputSectionVersionRequest",
    "ApplyTemplateToSectionRequest",
    # Backward compatibility aliases
    "CsrSectionBase",
    "CsrSectionRead",
    "CsrSectionVersionBase",
    "CsrSectionVersionCreate",
    "CsrSectionVersionRead",
    "CsrDocumentRead",
]
