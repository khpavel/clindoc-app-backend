from datetime import datetime
from typing import Any

from sqlalchemy import Integer, String, Text, DateTime, Boolean, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Template(Base):
    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "section_text", "prompt"
    section_code: Mapped[str | None] = mapped_column(String(100), nullable=True)  # e.g. "SYNOPSIS", "EFFICACY"
    language: Mapped[str] = mapped_column(String(10), nullable=False, server_default="en")
    scope: Mapped[str] = mapped_column(String(50), nullable=False, server_default="global")  # e.g. "global", "sponsor", "study"
    sponsor_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # keep for future use
    study_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # keep for future use
    content: Mapped[str] = mapped_column(Text, nullable=False)  # template body with {{variables}}
    variables: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)  # optional metadata about variables
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

