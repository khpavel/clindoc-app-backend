from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.study import Study


class CsrDocument(Base):
    __tablename__ = "csr_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    study_id: Mapped[int] = mapped_column(Integer, ForeignKey("studies.id"), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")

    # Relationships
    study: Mapped["Study"] = relationship("Study", back_populates="csr_document")
    sections: Mapped[list["CsrSection"]] = relationship(
        "CsrSection", back_populates="document", order_by="CsrSection.order_index"
    )


class CsrSection(Base):
    __tablename__ = "csr_sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("csr_documents.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "SYNOPSIS", "EFFICACY_PRIMARY"
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    document: Mapped["CsrDocument"] = relationship("CsrDocument", back_populates="sections")
    versions: Mapped[list["CsrSectionVersion"]] = relationship("CsrSectionVersion", back_populates="section")


class CsrSectionVersion(Base):
    __tablename__ = "csr_section_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    section_id: Mapped[int] = mapped_column(Integer, ForeignKey("csr_sections.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source: Mapped[str | None] = mapped_column(String(30), nullable=True)  # e.g. "human", "ai"

    # Relationships
    section: Mapped["CsrSection"] = relationship("CsrSection", back_populates="versions")

