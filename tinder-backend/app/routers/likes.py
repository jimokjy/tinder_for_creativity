"""
Роуты для лайков.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user_id
from app.models import Creation, Like
from app.schemas import LikeToggleOut

router = APIRouter(prefix="/likes", tags=["likes"])


@router.post("/{creation_id}", response_model=LikeToggleOut, status_code=201)
def like_creation(
    creation_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Поставить лайк. Один зритель — один лайк на творение."""
    creation = db.query(Creation).filter(Creation.id == creation_id).first()
    if not creation:
        raise HTTPException(status_code=404, detail="Творение не найдено")

    existing = (
        db.query(Like)
        .filter(Like.creation_id == creation_id, Like.viewer_session_id == user_id)
        .first()
    )
    if existing:
        # Уже лайкал — просто возвращаем текущее состояние, без ошибки.
        return LikeToggleOut(creation_id=creation_id, liked=True, likes_count=creation.likes_count)

    like = Like(creation_id=creation_id, viewer_session_id=user_id)
    db.add(like)
    creation.likes_count += 1

    try:
        db.commit()
    except IntegrityError:
        # На случай гонки двух одновременных запросов от одного и того же клиента.
        db.rollback()
        creation = db.query(Creation).filter(Creation.id == creation_id).first()
        return LikeToggleOut(creation_id=creation_id, liked=True, likes_count=creation.likes_count)

    db.refresh(creation)
    return LikeToggleOut(creation_id=creation_id, liked=True, likes_count=creation.likes_count)


@router.delete("/{creation_id}", response_model=LikeToggleOut)
def unlike_creation(
    creation_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Убрать свой лайк (на случай, если пользователь передумал)."""
    creation = db.query(Creation).filter(Creation.id == creation_id).first()
    if not creation:
        raise HTTPException(status_code=404, detail="Творение не найдено")

    like = (
        db.query(Like)
        .filter(Like.creation_id == creation_id, Like.viewer_session_id == user_id)
        .first()
    )
    if like:
        db.delete(like)
        creation.likes_count = max(0, creation.likes_count - 1)
        db.commit()
        db.refresh(creation)

    return LikeToggleOut(creation_id=creation_id, liked=False, likes_count=creation.likes_count)
