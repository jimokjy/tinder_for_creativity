"""
Вход через ЛК Силаэдра (OpenID Connect).

Схема:
  1. GET /auth/silaeder/login     — редирект браузера на lk.silaeder.ru
  2. пользователь логинится там
  3. GET /auth/silaeder/callback  — Силаэдр возвращает code, мы меняем его
     на токены, получаем userinfo (sub/email/name/roles) и решаем, что
     делать: войти в уже привязанный аккаунт, создать новый или запросить
     подтверждение привязки по email.

Правила привязки (см. silaeder-oidc.md):
  - Внешняя учётка идентифицируется только парой (issuer, sub).
    Email для автоматической привязки не используется.
  - Новый email создаёт новый локальный аккаунт.
  - Если локальный аккаунт с таким email уже существует — на этот адрес
    отправляется одноразовая ссылка (30 минут). Привязка происходит
    только после перехода по ней.
  - Роль, имя и email обновляются из userinfo при каждом входе.
"""
import re
from datetime import datetime, timedelta

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import (
    CRM_OIDC_ENABLED,
    CRM_OIDC_ISSUER,
    CRM_OIDC_REDIRECT_URI,
    APP_URL,
    OIDC_LINK_TOKEN_EXPIRE_MINUTES,
)
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, OidcIdentity, OidcLinkToken
from app.oidc_client import oauth
from app.security import set_auth_cookie, generate_link_token
from app.mailer import send_link_confirmation_email

router = APIRouter(prefix="/auth/silaeder", tags=["oidc"])

# Внешняя роль "admin" всегда преобразуется в локальную "teacher".
ROLE_MAP = {"admin": "teacher"}


def _require_enabled():
    if not CRM_OIDC_ENABLED:
        raise HTTPException(status_code=404, detail="Вход через ЛК Силаэдра выключен")


def _map_role(raw_roles) -> str | None:
    if not raw_roles:
        return None
    roles = raw_roles if isinstance(raw_roles, list) else [raw_roles]
    mapped = [ROLE_MAP.get(r, r) for r in roles]
    if "teacher" in mapped:
        return "teacher"
    if "student" in mapped:
        return "student"
    return mapped[0] if mapped else None


def _apply_userinfo(user: User, email: str | None, name: str | None, role: str | None) -> None:
    """Роль, имя и email обновляются из userinfo при каждом входе."""
    if email:
        user.email = email
    if name:
        user.display_name = name
    if role:
        user.external_role = role


_TRANSLIT_MAP = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}


def _transliterate(text: str) -> str:
    return "".join(_TRANSLIT_MAP.get(ch, ch) for ch in text.lower())


def _generate_username(db: Session, seed: str | None) -> str:
    # Имя из userinfo часто кириллическое (например, "Иван Иванов") — без
    # транслитерации регулярка ниже вырезала бы все буквы и оставляла
    # только "_", из-за чего у всех таких пользователей был бы
    # практически одинаковый пустой логин.
    transliterated = _transliterate(seed or "user")
    base = re.sub(r"[^a-zA-Z0-9_]", "", transliterated.replace(" ", "_"))[:20].lower() or "user"
    candidate = base
    suffix = 0
    while db.query(User).filter(User.username == candidate).first():
        suffix += 1
        candidate = f"{base}{suffix}"
    return candidate


@router.get("/login")
async def login(request: Request):
    """Начать вход через Силаэдр (используется и для регистрации — если
    внешней учётки ещё нет, при callback создастся новый локальный аккаунт)."""
    _require_enabled()
    request.session.pop("oidc_link_user_id", None)
    return await oauth.silaeder.authorize_redirect(request, CRM_OIDC_REDIRECT_URI)


@router.get("/link")
async def link_start(request: Request, current_user: User = Depends(get_current_user)):
    """Явная привязка ЛК Силаэдра к уже открытому у пользователя аккаунту
    (кнопка "Привязать ЛК Силаэдра" в настройках профиля)."""
    _require_enabled()
    request.session["oidc_link_user_id"] = current_user.id
    return await oauth.silaeder.authorize_redirect(request, CRM_OIDC_REDIRECT_URI)


@router.get("/logout/callback")
def logout_callback():
    """
    Зарегистрирован в ЛК Силаэдра как Post-logout Redirect URI. Полноценный
    единый выход (redirect на end_session_endpoint провайдера при обычном
    /auth/logout) пока не реализован — этот эндпоинт просто принимает
    редирект обратно, чтобы регистрация клиента в CRM не ломалась.
    """
    return RedirectResponse(f"{APP_URL}/login")


@router.get("/callback")
async def callback(request: Request, db: Session = Depends(get_db)):
    _require_enabled()

    try:
        token = await oauth.silaeder.authorize_access_token(request)
    except Exception:
        return RedirectResponse(f"{APP_URL}/login?silaeder_error=auth_failed")

    userinfo = token.get("userinfo")
    if not userinfo:
        userinfo = await oauth.silaeder.userinfo(token=token)

    sub = userinfo.get("sub")
    email = userinfo.get("email")
    name = userinfo.get("name")
    role = _map_role(userinfo.get("roles"))

    if not sub:
        return RedirectResponse(f"{APP_URL}/login?silaeder_error=no_sub")

    link_user_id = request.session.pop("oidc_link_user_id", None)

    identity = (
        db.query(OidcIdentity)
        .filter(OidcIdentity.issuer == CRM_OIDC_ISSUER, OidcIdentity.sub == sub)
        .first()
    )

    # --- Явная привязка через кнопку в настройках профиля ---
    if link_user_id:
        if identity and identity.user_id != link_user_id:
            return RedirectResponse(f"{APP_URL}/profile?silaeder_error=already_linked")

        target_user = db.query(User).filter(User.id == link_user_id).first()
        if not target_user:
            return RedirectResponse(f"{APP_URL}/login?silaeder_error=user_not_found")

        if not identity:
            db.add(OidcIdentity(user_id=target_user.id, issuer=CRM_OIDC_ISSUER, sub=sub))

        _apply_userinfo(target_user, email, name, role)
        db.commit()

        response = RedirectResponse(f"{APP_URL}/profile?silaeder_linked=1")
        set_auth_cookie(response, target_user.id, target_user.username)
        return response

    # --- Повторный вход через уже привязанную внешнюю учётку ---
    if identity:
        user = db.query(User).filter(User.id == identity.user_id).first()
        if not user:
            return RedirectResponse(f"{APP_URL}/login?silaeder_error=user_not_found")

        _apply_userinfo(user, email, name, role)
        db.commit()

        response = RedirectResponse(f"{APP_URL}/")
        set_auth_cookie(response, user.id, user.username)
        return response

    # --- Первый вход через эту внешнюю учётку ---
    existing_by_email = db.query(User).filter(User.email == email).first() if email else None

    if existing_by_email:
        # Email уже занят локальным аккаунтом — не привязываем автоматически,
        # отправляем одноразовую ссылку подтверждения.
        raw_token = generate_link_token()
        db.add(
            OidcLinkToken(
                token=raw_token,
                user_id=existing_by_email.id,
                issuer=CRM_OIDC_ISSUER,
                sub=sub,
                external_email=email,
                external_name=name,
                external_role=role,
                expires_at=datetime.utcnow() + timedelta(minutes=OIDC_LINK_TOKEN_EXPIRE_MINUTES),
            )
        )
        db.commit()
        send_link_confirmation_email(existing_by_email.email, raw_token)
        return RedirectResponse(f"{APP_URL}/login?silaeder_pending=1")

    # Совсем новый пользователь — создаём аккаунт без пароля
    # (войти в него можно только через Силаэдр).
    new_user = User(
        username=_generate_username(db, name or (email.split("@")[0] if email else None)),
        password_hash=None,
        email=email,
        display_name=name,
        external_role=role,
    )
    db.add(new_user)
    db.flush()
    db.add(OidcIdentity(user_id=new_user.id, issuer=CRM_OIDC_ISSUER, sub=sub))
    db.commit()

    response = RedirectResponse(f"{APP_URL}/")
    set_auth_cookie(response, new_user.id, new_user.username)
    return response


@router.get("/link-confirm")
def link_confirm(token: str, db: Session = Depends(get_db)):
    """Переход по одноразовой ссылке из письма — подтверждает привязку."""
    _require_enabled()

    link_token = db.query(OidcLinkToken).filter(OidcLinkToken.token == token).first()
    if not link_token or link_token.used or link_token.expires_at < datetime.utcnow():
        return RedirectResponse(f"{APP_URL}/login?silaeder_error=link_expired")

    user = db.query(User).filter(User.id == link_token.user_id).first()
    if not user:
        return RedirectResponse(f"{APP_URL}/login?silaeder_error=user_not_found")

    already_linked = (
        db.query(OidcIdentity)
        .filter(OidcIdentity.issuer == link_token.issuer, OidcIdentity.sub == link_token.sub)
        .first()
    )
    if not already_linked:
        db.add(OidcIdentity(user_id=user.id, issuer=link_token.issuer, sub=link_token.sub))

    _apply_userinfo(user, link_token.external_email, link_token.external_name, link_token.external_role)
    link_token.used = True
    db.commit()

    response = RedirectResponse(f"{APP_URL}/")
    set_auth_cookie(response, user.id, user.username)
    return response
