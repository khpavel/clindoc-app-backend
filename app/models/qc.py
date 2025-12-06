from datetime import datetime
from typing import TYPE_CHECKING, Optional
from enum import Enum

from sqlalchemy import ForeignKey, Integer, String, Text, DateTime, Boolean, func, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.study import Study
    from app.models.output_document import OutputDocument, OutputSection


class QCRuleSeverity(str, Enum):
    """Серьёзность правила QC."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class QCIssueStatus(str, Enum):
    """Статус QC issue."""
    OPEN = "open"
    RESOLVED = "resolved"
    WONT_FIX = "wont_fix"


class QCRule(Base):
    __tablename__ = "qc_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=QCRuleSeverity.INFO.value
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    issues: Mapped[list["QCIssue"]] = relationship("QCIssue", back_populates="rule")

    __table_args__ = (
        CheckConstraint(
            "severity IN ('info', 'warning', 'error')",
            name="check_qc_rule_severity"
        ),
    )


class QCIssue(Base):
    __tablename__ = "qc_issues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    study_id: Mapped[int] = mapped_column(Integer, ForeignKey("studies.id"), nullable=False, index=True)
    document_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("output_documents.id"), nullable=True, index=True)
    section_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("output_sections.id"), nullable=True, index=True)
    rule_id: Mapped[int] = mapped_column(Integer, ForeignKey("qc_rules.id"), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=QCIssueStatus.OPEN.value)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    study: Mapped["Study"] = relationship("Study")
    document: Mapped[Optional["OutputDocument"]] = relationship("OutputDocument")
    section: Mapped[Optional["OutputSection"]] = relationship("OutputSection")
    rule: Mapped["QCRule"] = relationship("QCRule", back_populates="issues")

    __table_args__ = (
        CheckConstraint(
            "severity IN ('info', 'warning', 'error')",
            name="check_qc_issue_severity"
        ),
        CheckConstraint(
            "status IN ('open', 'resolved', 'wont_fix')",
            name="check_qc_issue_status"
        ),
    )
