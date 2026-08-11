"""
Сохранение загруженных файлов.

Сейчас файлы кладутся на локальный диск в UPLOAD_DIR и раздаются
через StaticFiles (см. main.py). Для продакшена достаточно заменить
save_upload_file() на загрузку в S3 / Cloudflare R2 / аналог —
остальной код (модели, роуты) менять не придётся, т.к. наружу
отдаётся просто file_url.
"""
import uuid
from pathlib import Path

from fastapi import UploadFile, HTTPException

from app.config import UPLOAD_DIR, MAX_UPLOAD_SIZE_MB, ALLOWED_EXTENSIONS
from app.models import MediaType


def detect_media_type(filename: str) -> MediaType:
    ext = Path(filename).suffix.lower()
    if ext in ALLOWED_EXTENSIONS["image"]:
        return MediaType.image
    if ext in ALLOWED_EXTENSIONS["audio"]:
        return MediaType.audio
    return MediaType.other


async def save_upload_file(file: UploadFile) -> tuple[str, MediaType]:
    """Сохраняет файл на диск, возвращает (публичный_путь, тип_медиа)."""
    ext = Path(file.filename).suffix.lower()
    all_allowed = ALLOWED_EXTENSIONS["image"] | ALLOWED_EXTENSIONS["audio"]
    if ext not in all_allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Недопустимый формат файла: {ext}. Разрешены: {sorted(all_allowed)}",
        )

    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"Файл слишком большой ({size_mb:.1f} МБ). Максимум {MAX_UPLOAD_SIZE_MB} МБ.",
        )

    stored_name = f"{uuid.uuid4()}{ext}"
    dest_path = UPLOAD_DIR / stored_name
    dest_path.write_bytes(contents)

    public_url = f"/uploads/{stored_name}"
    return public_url, detect_media_type(file.filename)
