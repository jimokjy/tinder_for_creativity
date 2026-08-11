"""
Роуты авторизации: регистрация, вход, выход, "кто я".

Токен выдаётся в httponly cookie — фронтенду не нужно самому хранить
и подставлять токен в заголовки, браузер делает это автоматически при
credentials: 'include'.
"""
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, OidcIdentity
from app.schemas import UserCreate, UserOut
from app.security import hash_password, verify_password, set_auth_cookie
from app.config import AUTH_COOKIE_NAME

router = APIRouter(prefix="/auth", tags=["auth"])


def _to_user_out(db: Session, user: User) -> UserOut:
    silaeder_linked = (
        db.query(OidcIdentity).filter(OidcIdentity.user_id == user.id).first() is not None
    )
    return UserOut(
        username=user.username,
        created_at=user.created_at,
        email=user.email,
        silaeder_linked=silaeder_linked,
    )


@router.post("/register", response_model=UserOut, status_code=201)
def register(payload: UserCreate, response: Response, db: Session = Depends(get_db)):
    user = User(username=payload.username, password_hash=hash_password(payload.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Такой логин уже занят")
    db.refresh(user)

    set_auth_cookie(response, user.id, user.username)
    return _to_user_out(db, user)


@router.post("/login", response_model=UserOut)
def login(payload: UserCreate, response: Response, db: Session = Depends(get_db)):
    # Переиспользуем UserCreate для входа — поля те же (username/password),
    # но валидация длины тут ни при чём, поэтому проверяем пароль напрямую.
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    set_auth_cookie(response, user.id, user.username)
    return _to_user_out(db, user)


@router.post("/logout", status_code=200)
def logout(response: Response):
    response.delete_cookie(AUTH_COOKIE_NAME)
    return {"status": "ok"}


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _to_user_out(db, current_user)
