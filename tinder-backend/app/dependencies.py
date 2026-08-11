"""
Зависимость авторизации: читает JWT из httponly cookie, проверяет его
и отдаёт id текущего пользователя. Используется во всех роутах, где
нужно знать "кто спрашивает" (публикация, лайки, лента, свои творения) —
но, как и раньше, этот id никогда не отдаётся наружу вместе с публичными
данными о творениях, так что для остальных пользователей всё
по-прежнему анонимно.
"""
from fastapi import Request, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.config import AUTH_COOKIE_NAME
from app.database import get_db
from app.models import User
from app.security import decode_access_token

UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Нужно войти в аккаунт",
)


def get_current_user_id(request: Request) -> str:
    """Лёгкая проверка: просто достаёт user_id из токена, без похода в БД."""
    token = request.cookies.get(AUTH_COOKIE_NAME)
    if not token:
        raise UNAUTHORIZED

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise UNAUTHORIZED

    return payload["sub"]


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Полная версия: возвращает объект User (используется в /auth/me)."""
    user_id = get_current_user_id(request)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UNAUTHORIZED
    return user
