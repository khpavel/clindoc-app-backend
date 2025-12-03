from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.csr import CsrDocument
    from app.models.source import SourceDocument


class Study(Base):
    __tablename__ = "studies"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    phase = Column(String(20), nullable=True)

    # Relationships
    csr_document: Mapped["CsrDocument | None"] = relationship("CsrDocument", back_populates="study", uselist=False)
    source_documents: Mapped[list["SourceDocument"]] = relationship("SourceDocument", back_populates="study", cascade="all, delete-orphan")
