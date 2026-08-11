"""
Роуты для публикации и управления своими творениями.
"""
from typing import Optional, List

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user_id
from app.models import Creation, MediaType, Report
from app.schemas import CreationOut, CreationWithStatsOut, ReportIn
from app.storage import save_upload_file
from app.config import AUTO_HIDE_REPORT_THRESHOLD

router = APIRouter(prefix="/creations", tags=["creations"])


@router.post("", response_model=CreationOut, status_code=201)
async def publish_creation(
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Опубликовать новое творение. Файл необязателен — можно опубликовать
    и чисто текстовое творение (например, стихотворение) без вложения.
    """
    if not file and not (description and description.strip()):
        raise HTTPException(
            status_code=400,
            detail="Нужно приложить файл или хотя бы добавить текстовое описание.",
        )

    file_url = None
    media_type = MediaType.text

    if file:
        file_url, media_type = await save_upload_file(file)

    creation = Creation(
        author_session_id=user_id,
        title=title,
        description=description,
        category=category,
        file_url=file_url,
        media_type=media_type,
    )
    db.add(creation)
    db.commit()
    db.refresh(creation)
    return creation


@router.get("/mine", response_model=List[CreationWithStatsOut])
def list_my_creations(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Список своих творений с количеством лайков — для автора."""
    creations = (
        db.query(Creation)
        .filter(Creation.author_session_id == user_id)
        .order_by(Creation.created_at.desc())
        .all()
    )
    return creations


@router.get("/{creation_id}", response_model=CreationOut)
def get_creation(creation_id: str, db: Session = Depends(get_db)):
    creation = db.query(Creation).filter(Creation.id == creation_id).first()
    if not creation:
        raise HTTPException(status_code=404, detail="Творение не найдено")
    return creation


@router.delete("/{creation_id}", status_code=204)
def delete_creation(
    creation_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Удалить своё творение (проверяем, что удаляет автор)."""
    creation = db.query(Creation).filter(Creation.id == creation_id).first()
    if not creation:
        raise HTTPException(status_code=404, detail="Творение не найдено")
    if creation.author_session_id != user_id:
        raise HTTPException(status_code=403, detail="Это не ваше творение")

    db.delete(creation)
    db.commit()
    return None


@router.post("/{creation_id}/report", status_code=201)
def report_creation(
    creation_id: str,
    payload: ReportIn,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Пожаловаться на творение. При накоплении жалоб — автоскрытие из ленты."""
    creation = db.query(Creation).filter(Creation.id == creation_id).first()
    if not creation:
        raise HTTPException(status_code=404, detail="Творение не найдено")

    report = Report(
        creation_id=creation_id,
        reporter_session_id=user_id,
        reason=payload.reason,
    )
    db.add(report)

    creation.report_count += 1
    if creation.report_count >= AUTO_HIDE_REPORT_THRESHOLD:
        creation.is_hidden = True

    db.commit()
    return {"status": "ok"}
