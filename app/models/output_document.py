from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.study import Study
    from app.models.document import Document


class OutputDocument(Base):
    __tablename__ = "output_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    study_id: Mapped[int] = mapped_column(Integer, ForeignKey("studies.id"), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    document_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("documents.id"), nullable=True, index=True)
    # Content language of the document ("ru" or "en")
    language: Mapped[str] = mapped_column(String(2), nullable=False, default="ru")

    # Relationships
    study: Mapped["Study"] = relationship("Study", back_populates="csr_document")
    document: Mapped["Document | None"] = relationship(
        "Document", 
        back_populates="csr_document", 
        uselist=False,
        foreign_keys=[document_id]
    )
    sections: Mapped[list["OutputSection"]] = relationship(
        "OutputSection", back_populates="document", order_by="OutputSection.order_index"
    )


class OutputSection(Base):
    __tablename__ = "output_sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("output_documents.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "SYNOPSIS", "EFFICACY_PRIMARY"
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    document: Mapped["OutputDocument"] = relationship("OutputDocument", back_populates="sections")
    versions: Mapped[list["OutputSectionVersion"]] = relationship("OutputSectionVersion", back_populates="section")


class OutputSectionVersion(Base):
    __tablename__ = "output_section_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    section_id: Mapped[int] = mapped_column(Integer, ForeignKey("output_sections.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source: Mapped[str | None] = mapped_column(String(30), nullable=True)  # e.g. "human", "ai", "template"
    template_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("templates.id"), nullable=True)

    # Relationships
    section: Mapped["OutputSection"] = relationship("OutputSection", back_populates="versions")

