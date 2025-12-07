from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.study import Study
    from app.models.output_document import OutputDocument


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    study_id: Mapped[int] = mapped_column(Integer, ForeignKey("studies.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "csr", "protocol", "ib"
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    template_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")  # e.g. "draft", "in_qc", "ready_for_submission", "archived"
    current_version_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Content language of the document ("ru" or "en")
    language: Mapped[str] = mapped_column(String(2), nullable=False, default="ru")
    created_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    study: Mapped["Study"] = relationship("Study", back_populates="documents")
    csr_document: Mapped["OutputDocument | None"] = relationship(
        "OutputDocument", 
        back_populates="document", 
        uselist=False
    )

