"""
Pydantic-схемы: что принимает и что отдаёт API.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.models import MediaType
from app.config import (
    MIN_USERNAME_LENGTH,
    MAX_USERNAME_LENGTH,
    MIN_PASSWORD_LENGTH,
)


class UserCreate(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if not (MIN_USERNAME_LENGTH <= len(v) <= MAX_USERNAME_LENGTH):
            raise ValueError(
                f"Логин должен быть от {MIN_USERNAME_LENGTH} до {MAX_USERNAME_LENGTH} символов"
            )
        if not v.replace("_", "").isalnum():
            raise ValueError("Логин может содержать только буквы, цифры и подчёркивание")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"Пароль должен быть не короче {MIN_PASSWORD_LENGTH} символов")
        return v


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    created_at: datetime
    email: Optional[str] = None
    silaeder_linked: bool = False


class CreationOut(BaseModel):
    """Творение, как оно отдаётся зрителю в ленте (без данных об авторе)."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: Optional[str]
    description: Optional[str]
    media_type: MediaType
    file_url: Optional[str]
    category: Optional[str]
    created_at: datetime


class CreationWithStatsOut(CreationOut):
    """То же самое, но с лайками — для страницы "мои творения" автора."""
    likes_count: int
    is_hidden: bool


class LikeToggleOut(BaseModel):
    creation_id: str
    liked: bool          # True — лайк поставлен, False — лайк снят
    likes_count: int      # актуальное количество лайков после действия


class ReportIn(BaseModel):
    reason: Optional[str] = None


class FeedResponse(BaseModel):
    """Ответ ленты: либо есть творение, либо куча закончилась."""
    creation: Optional[CreationOut] = None
    exhausted: bool = False  # True, если больше нечего показывать
