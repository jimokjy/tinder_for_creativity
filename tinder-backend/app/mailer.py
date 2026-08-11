"""
Отправка одноразовой ссылки подтверждения привязки аккаунта Силаэдра.

Настраивается через переменные MAIL_* (см. .env.example). Если MAIL_HOST
не задан, письмо не отправляется, а ссылка просто пишется в лог сервера —
удобно для локальной разработки без настроенного SMTP.
"""
import logging
import smtplib
from email.mime.text import MIMEText

from app.config import (
    MAIL_HOST,
    MAIL_PORT,
    MAIL_USERNAME,
    MAIL_PASSWORD,
    MAIL_FROM,
    MAIL_USE_TLS,
    APP_URL,
)

logger = logging.getLogger("app.mailer")


def send_link_confirmation_email(to_email: str, token: str) -> None:
    # Публичный путь /auth/silaeder/link-confirm проксируется на бэкенд
    # так же, как /auth/silaeder/callback (см. next.config.js).
    link = f"{APP_URL}/auth/silaeder/link-confirm?token={token}"

    subject = "Подтверждение привязки ЛК Силаэдра"
    body = (
        "Здравствуйте!\n\n"
        "Кто-то попытался войти на сайт через ЛК Силаэдра с этим email, "
        "и на сайте уже есть аккаунт с таким же адресом.\n\n"
        f"Если это были вы — подтвердите привязку по ссылке "
        f"(действует 30 минут):\n{link}\n\n"
        "Если это были не вы — просто проигнорируйте это письмо, "
        "привязка не произойдёт."
    )

    if not MAIL_HOST:
        logger.warning(
            "MAIL_HOST не настроен — письмо не отправлено. "
            "Ссылка подтверждения для %s: %s",
            to_email,
            link,
        )
        return

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = MAIL_FROM
    msg["To"] = to_email

    with smtplib.SMTP(MAIL_HOST, MAIL_PORT, timeout=10) as server:
        if MAIL_USE_TLS:
            server.starttls()
        if MAIL_USERNAME:
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.send_message(msg)
