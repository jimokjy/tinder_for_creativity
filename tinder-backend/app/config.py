"""
Настройки приложения.
Значения читаются из переменных окружения (см. .env.example),
но для локального старта заданы разумные значения по умолчанию.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Подхватываем переменные из .env в окружение процесса.
# Без этого os.getenv() ниже будет видеть только то, что явно
# экспортировано в терминале, а сам файл .env читаться не будет.
load_dotenv(BASE_DIR / ".env")

# Строка подключения к БД.
# Для старта используем SQLite (не требует установки сервера БД).
# В проде замените на PostgreSQL, например:
#   postgresql+psycopg2://user:password@localhost:5432/creations_db
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'app.db'}")

# Куда сохраняются загруженные файлы (картинки/аудио).
# В проде лучше заменить на S3 / аналог (см. app/storage.py).
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", BASE_DIR / "uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Имя cookie, в которой хранится анонимный идентификатор пользователя.
SESSION_COOKIE_NAME = "anon_session_id"
SESSION_COOKIE_MAX_AGE = 60 * 60 * 24 * 365 * 2  # 2 года

# Ограничения на загрузку файлов.
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "20"))
ALLOWED_EXTENSIONS = {
    "image": {".jpg", ".jpeg", ".png", ".gif", ".webp"},
    "audio": {".mp3", ".wav", ".ogg", ".m4a"},
}

# Разрешённые источники для CORS (адреса вашего фронтенда).
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

# После скольких жалоб творение автоматически скрывается из ленты.
AUTO_HIDE_REPORT_THRESHOLD = int(os.getenv("AUTO_HIDE_REPORT_THRESHOLD", "5"))

# --- Авторизация (логин/пароль) ---

# Секрет для подписи JWT-токенов. ОБЯЗАТЕЛЬНО замените на свою случайную
# строку в продакшене (например: python -c "import secrets; print(secrets.token_hex(32))"),
# иначе токены можно будет подделать.
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = int(os.getenv("JWT_EXPIRE_DAYS", "30"))

AUTH_COOKIE_NAME = "access_token"
AUTH_COOKIE_MAX_AGE = JWT_EXPIRE_DAYS * 24 * 60 * 60

MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 30
MIN_PASSWORD_LENGTH = 6

# --- Вход через ЛК Силаэдра (OpenID Connect) ---

# Публичный адрес сайта (фронтенда) — сюда редиректим браузер после
# успешного/неуспешного входа через Силаэдр.
APP_URL = os.getenv("APP_URL", "http://localhost:3000")

CRM_OIDC_ENABLED = os.getenv("CRM_OIDC_ENABLED", "false").lower() == "true"
CRM_OIDC_ISSUER = os.getenv("CRM_OIDC_ISSUER", "https://lk.silaeder.ru")
CRM_OIDC_CLIENT_ID = os.getenv("CRM_OIDC_CLIENT_ID", "")
CRM_OIDC_CLIENT_SECRET = os.getenv("CRM_OIDC_CLIENT_SECRET", "")
# Публичный адрес callback-эндпоинта, зарегистрированный в ЛК Силаэдра
# как Redirect URI, например https://example.ru/auth/silaeder/callback
CRM_OIDC_REDIRECT_URI = os.getenv("CRM_OIDC_REDIRECT_URI", "")

# Секрет для подписи временной cookie-сессии, в которой authlib хранит
# state/nonce на время OIDC-хендшейка (пара редиректов туда-обратно).
# Никак не связан с JWT из access_token — это отдельный, короткоживущий механизм.
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "dev-session-secret-change-me")

# Сколько живёт одноразовая ссылка подтверждения привязки аккаунта
# (когда email из Силаэдра совпал с уже существующим локальным аккаунтом).
OIDC_LINK_TOKEN_EXPIRE_MINUTES = 30

# --- Почта (для ссылки подтверждения привязки аккаунта) ---
# Если MAIL_HOST не задан, ссылка не отправляется, а пишется в лог сервера —
# удобно для локальной разработки без настроенного SMTP.
MAIL_HOST = os.getenv("MAIL_HOST", "")
MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
MAIL_FROM = os.getenv("MAIL_FROM", "") or MAIL_USERNAME
MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
