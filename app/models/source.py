from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, DateTime, Boolean, func, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.study import Study


class SourceDocument(Base):
    __tablename__ = "source_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    study_id: Mapped[int] = mapped_column(Integer, ForeignKey("studies.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "protocol", "sap", "tlf", "csr_prev"
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)  # relative path on disk or S3 key
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    uploaded_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # New fields
    language: Mapped[str] = mapped_column(String(2), nullable=False, default="ru")  # "ru" or "en"
    version_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")  # "active", "superseded", "archived"
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_rag_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    index_status: Mapped[str] = mapped_column(String(20), nullable=False, default="not_indexed")  # "not_indexed", "indexed", "error"

    # Relationships
    study: Mapped["Study"] = relationship("Study", back_populates="source_documents")
    
    __table_args__ = (
        CheckConstraint("language IN ('ru', 'en')", name="ck_source_document_language"),
        CheckConstraint("status IN ('active', 'superseded', 'archived')", name="ck_source_document_status"),
        CheckConstraint("index_status IN ('not_indexed', 'indexed', 'error')", name="ck_source_document_index_status"),
    )

