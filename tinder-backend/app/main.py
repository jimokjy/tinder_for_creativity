"""
Точка входа приложения.

Запуск для разработки:
    uvicorn app.main:app --reload

Документация API (Swagger) будет доступна на:
    http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import CORS_ORIGINS, UPLOAD_DIR, SESSION_SECRET_KEY
from app.database import Base, engine
from app.routers import auth, creations, feed, likes, oidc

# Создаёт таблицы при старте, если их ещё нет.
# Для реального продакшена лучше перейти на миграции (Alembic),
# чтобы безопасно менять схему БД без потери данных.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Creations Feed API",
    description="Бэкенд для анонимного 'тиндера творчества': публикация работ, "
                 "случайная лента и лайки.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,  # обязательно для работы cookie-сессий с фронтендом
    allow_methods=["*"],
    allow_headers=["*"],
)

# Нужен только для authlib: хранит одноразовые state/nonce на время
# OIDC-хендшейка (пара редиректов на Силаэдр и обратно). Никак не связан
# с нашей собственной auth-cookie (см. app/security.py).
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY, same_site="lax")

# Раздача загруженных файлов по /uploads/<filename>
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

app.include_router(auth.router)
app.include_router(oidc.router)
app.include_router(creations.router)
app.include_router(feed.router)
app.include_router(likes.router)


@app.get("/health", tags=["service"])
def health_check():
    return {"status": "ok"}
