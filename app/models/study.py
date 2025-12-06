from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.csr import CsrDocument
    from app.models.source import SourceDocument
    from app.models.study_member import StudyMember
    from app.models.document import Document


class StudyStatus(str, Enum):
    """Статусы исследования."""
    DRAFT = "draft"
    ONGOING = "ongoing"
    CLOSED = "closed"
    ARCHIVED = "archived"


class Study(Base):
    __tablename__ = "studies"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    phase = Column(String(20), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # TODO: Make non-nullable after data migration
    status = Column(SQLEnum(StudyStatus, native_enum=False, length=20), nullable=False, default=StudyStatus.DRAFT)
    indication = Column(String(255), nullable=True)
    sponsor_name = Column(String(255), nullable=True)

    # Relationships
    csr_document: Mapped["CsrDocument | None"] = relationship("CsrDocument", back_populates="study", uselist=False)
    source_documents: Mapped[list["SourceDocument"]] = relationship("SourceDocument", back_populates="study", cascade="all, delete-orphan")
    members: Mapped[list["StudyMember"]] = relationship("StudyMember", back_populates="study", cascade="all, delete-orphan")
    documents: Mapped[list["Document"]] = relationship("Document", back_populates="study", cascade="all, delete-orphan")
