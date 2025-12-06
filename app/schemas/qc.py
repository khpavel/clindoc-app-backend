from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class QCRuleBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    severity: str  # "info", "warning", "error"
    is_active: bool = True


class QCRuleRead(QCRuleBase):
    id: int

    class Config:
        from_attributes = True


class QCIssueBase(BaseModel):
    study_id: int
    document_id: Optional[int] = None
    section_id: Optional[int] = None
    rule_id: int
    severity: str  # "info", "warning", "error"
    status: str  # "open", "resolved", "wont_fix"
    message: str


class QCIssueRead(QCIssueBase):
    id: int
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

    class Config:
        from_attributes = True


class QCIssueListResponse(BaseModel):
    issues: list[QCIssueRead]
    total: int


class QCRunResponse(BaseModel):
    document_id: int
    issues_created: int
    message: str
