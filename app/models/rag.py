from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.source import SourceDocument


class RagChunk(Base):
    __tablename__ = "rag_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    study_id: Mapped[int] = mapped_column(Integer, nullable=False)
    source_document_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("source_documents.id"), nullable=True
    )
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "protocol", "sap", "tlf", "csr_prev"
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)  # порядковый номер чанка в документе
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    source_document: Mapped["SourceDocument | None"] = relationship("SourceDocument")

    __table_args__ = (
        Index("ix_rag_chunks_study_source_order", "study_id", "source_type", "order_index"),
    )

