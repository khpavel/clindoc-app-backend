from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.study import Study


class CsrDocument(Base):
    __tablename__ = "csr_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    study_id: Mapped[int] = mapped_column(Integer, ForeignKey("studies.id"), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "draft", "in_review", "final"

    # Relationships
    study: Mapped["Study"] = relationship("Study", back_populates="csr_document")
    sections: Mapped[list["CsrSection"]] = relationship("CsrSection", back_populates="document", cascade="all, delete-orphan")


class CsrSection(Base):
    __tablename__ = "csr_sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("csr_documents.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "EFFICACY_PRIMARY"
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    document: Mapped["CsrDocument"] = relationship("CsrDocument", back_populates="sections")
    versions: Mapped[list["CsrSectionVersion"]] = relationship("CsrSectionVersion", back_populates="section", cascade="all, delete-orphan")


class CsrSectionVersion(Base):
    __tablename__ = "csr_section_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    section_id: Mapped[int] = mapped_column(Integer, ForeignKey("csr_sections.id"), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "human" / "ai"

    # Relationships
    section: Mapped["CsrSection"] = relationship("CsrSection", back_populates="versions")

