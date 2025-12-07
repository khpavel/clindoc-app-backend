from pydantic import BaseModel, field_validator


class UserBase(BaseModel):
    username: str
    full_name: str | None = None
    email: str | None = None


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int
    is_active: bool
    ui_language: str

    class Config:
        orm_mode = True


class UserUpdate(BaseModel):
    username: str | None = None
    full_name: str | None = None
    email: str | None = None
    ui_language: str | None = None
    
    @field_validator("ui_language")
    @classmethod
    def validate_ui_language(cls, v):
        if v is not None and v not in {"ru", "en"}:
            raise ValueError("ui_language must be 'ru' or 'en'")
        return v


class UserMe(UserRead):
    """Schema for /users/me endpoint - same as UserRead but more explicit."""
    pass


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None

