"""
Хэширование паролей и выдача/проверка JWT-токенов для авторизации.
"""
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Response
from jwt import InvalidTokenError

from app.config import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    JWT_EXPIRE_DAYS,
    AUTH_COOKIE_NAME,
    AUTH_COOKIE_MAX_AGE,
)


def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(user_id: str, username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRE_DAYS)
    payload = {"sub": user_id, "username": username, "exp": expire}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Возвращает payload токена, либо None если он невалиден/просрочен."""
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except InvalidTokenError:
        return None


def set_auth_cookie(response: Response, user_id: str, username: str) -> None:
    """Выдаёт нашу обычную auth-cookie — общая точка для обычного логина и OIDC."""
    token = create_access_token(user_id, username)
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        max_age=AUTH_COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        # secure=True,  # включите, когда сайт будет на https
    )


def generate_link_token() -> str:
    """Случайный токен для одноразовой ссылки подтверждения привязки аккаунта."""
    return secrets.token_urlsafe(32)
