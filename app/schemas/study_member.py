from datetime import datetime
from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, Field

from app.schemas.user import UserRead


class StudyMemberRole(str, Enum):
    """Роли участника исследования."""
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class StudyMemberAddPayload(BaseModel):
    """Схема для добавления участника исследования (user_id передается в path)."""
    role: Literal["owner", "editor", "viewer"] = Field(..., description="Роль участника: owner, editor, viewer")


class UserShort(BaseModel):
    """Укороченная схема пользователя для вложенных объектов."""
    id: int
    username: str
    full_name: Optional[str] = None
    email: Optional[str] = None

    class Config:
        orm_mode = True


class StudyMemberRead(BaseModel):
    """Схема для чтения участника исследования."""
    id: int
    study_id: int
    user_id: int
    role: str
    created_at: datetime
    user: UserRead | None = None  # Опциональные данные пользователя

    class Config:
        orm_mode = True


class StudyMemberMeResponse(BaseModel):
    """Схема ответа для получения роли текущего пользователя в исследовании."""
    id: int
    study_id: int
    user_id: int
    role: str  # "owner" | "editor" | "viewer"
    created_at: datetime
    user: UserShort

    class Config:
        orm_mode = True

