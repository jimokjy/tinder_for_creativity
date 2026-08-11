"""
Модели базы данных.

Ключевая идея анонимности: у каждого посетителя есть session_id
(UUID, хранится в cookie у него в браузере, см. app/dependencies.py).
Он используется и как "автор" при публикации, и как "зритель" при лайках —
никакой регистрации или личных данных не требуется.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Text, DateTime, ForeignKey, Integer,
    Enum, Boolean, UniqueConstraint, Index,
)
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class MediaType(str, enum.Enum):
    image = "image"
    audio = "audio"
    text = "text"
    other = "other"


class User(Base):
    """
    Аккаунт пользователя. Наружу (в ленте, в лайках) никакие данные
    аккаунта никогда не показываются — публикации и лайки остаются
    анонимными, аккаунт нужен только чтобы не терять доступ к своим
    публикациям между заходами/устройствами.

    Можно завести обычной регистрацией (username+password) или входом
    через ЛК Силаэдра (тогда пароля у аккаунта нет — password_hash пуст,
    а вход возможен только через Силаэдр).
    """
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    username = Column(String(30), unique=True, index=True, nullable=False)
    # Пусто у аккаунтов, заведённых только через ЛК Силаэдра.
    password_hash = Column(String, nullable=True)

    # Ниже — данные, которые приходят только из ЛК Силаэдра (userinfo).
    # У аккаунтов с обычной регистрацией (username+password) остаются пустыми.
    email = Column(String, unique=True, index=True, nullable=True)
    display_name = Column(String, nullable=True)
    external_role = Column(String, nullable=True)  # student / teacher (admin -> teacher)

    created_at = Column(DateTime, default=datetime.utcnow)


class OidcIdentity(Base):
    """
    Привязка внешней учётки ЛК Силаэдра к локальному аккаунту.
    Идентифицируется только парой (issuer, sub) — email для этого
    не используется, см. app/routers/oidc.py.
    """
    __tablename__ = "oidc_identities"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    issuer = Column(String, nullable=False)
    sub = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("issuer", "sub", name="uq_oidc_issuer_sub"),
    )


class OidcLinkToken(Base):
    """
    Одноразовая ссылка подтверждения привязки — выдаётся, когда при первом
    входе через Силаэдр выясняется, что email из userinfo уже занят
    существующим локальным аккаунтом. Привязка происходит только после
    перехода по этой ссылке (шлётся на email), не автоматически.
    """
    __tablename__ = "oidc_link_tokens"

    id = Column(String, primary_key=True, default=gen_uuid)
    token = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    issuer = Column(String, nullable=False)
    sub = Column(String, nullable=False)
    external_email = Column(String, nullable=True)
    external_name = Column(String, nullable=True)
    external_role = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Creation(Base):
    """Одно творение — фото, аудио, текст и т.п."""
    __tablename__ = "creations"

    id = Column(String, primary_key=True, default=gen_uuid)

    # Идентификатор автора — id аккаунта (User.id). Хранится, чтобы автор
    # мог видеть свои творения и статистику, но нигде не отдаётся наружу
    # вместе с публичными данными о творении (в ленте и т.п. остаётся анонимным).
    author_session_id = Column(String, index=True, nullable=False)

    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)

    media_type = Column(Enum(MediaType), nullable=False, default=MediaType.image)
    file_url = Column(String, nullable=True)  # ссылка/путь к файлу, если есть
    category = Column(String(50), nullable=True, index=True)

    likes_count = Column(Integer, nullable=False, default=0)
    report_count = Column(Integer, nullable=False, default=0)
    is_hidden = Column(Boolean, nullable=False, default=False)  # скрыто модерацией

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    likes = relationship("Like", back_populates="creation", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="creation", cascade="all, delete-orphan")


class Like(Base):
    """Лайк от анонимного зрителя творению."""
    __tablename__ = "likes"

    id = Column(String, primary_key=True, default=gen_uuid)
    creation_id = Column(String, ForeignKey("creations.id"), nullable=False)
    viewer_session_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    creation = relationship("Creation", back_populates="likes")

    __table_args__ = (
        # Один и тот же зритель не может лайкнуть одно творение дважды.
        UniqueConstraint("creation_id", "viewer_session_id", name="uq_like_once"),
        Index("ix_likes_creation_viewer", "creation_id", "viewer_session_id"),
    )


class Seen(Base):
    """
    Какие творения уже показывались данному зрителю в ленте.
    Нужно, чтобы не подсовывать одно и то же по кругу
    (лайкнутые уже исключаются через таблицу Like, а это — для пропущенных).
    """
    __tablename__ = "seen"

    id = Column(String, primary_key=True, default=gen_uuid)
    creation_id = Column(String, ForeignKey("creations.id"), nullable=False)
    viewer_session_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("creation_id", "viewer_session_id", name="uq_seen_once"),
    )


class Report(Base):
    """Жалоба на творение (для базовой модерации)."""
    __tablename__ = "reports"

    id = Column(String, primary_key=True, default=gen_uuid)
    creation_id = Column(String, ForeignKey("creations.id"), nullable=False)
    reporter_session_id = Column(String, nullable=False)
    reason = Column(String(300), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    creation = relationship("Creation", back_populates="reports")
