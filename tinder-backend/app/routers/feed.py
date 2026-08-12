"""
Роут ленты: отдаёт случайное, ещё не увиденное творение из "кучи".
"""
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.dependencies import get_current_user_id
from app.models import Creation, Like, Seen
from app.schemas import FeedResponse

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("/random", response_model=FeedResponse)
def get_random_creation(
    category: Optional[str] = Query(None, description="Показывать только эту категорию"),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Возвращает одно случайное творение, которое этот зритель:
      - ещё не лайкал,
      - ещё не видел (не пропускал) в ленте,
      - и которое не является его собственным.
    Также исключаются скрытые модерацией творения.
    Если передан ``category`` — дополнительно фильтрует только по ней.

    Важно: ORDER BY RANDOM() в SQL на больших таблицах (миллионы строк)
    работает медленно, т.к. требует полного скана. Для MVP этого достаточно.
    При росте базы стоит заменить на выборку по случайному индексу
    (например, хранить у творения случайное число и делать
    WHERE rand_key > :random_seed ORDER BY rand_key LIMIT 1).
    """
    already_liked = db.query(Like.creation_id).filter(Like.viewer_session_id == user_id)
    already_seen = db.query(Seen.creation_id).filter(Seen.viewer_session_id == user_id)

    query = db.query(Creation).filter(
        Creation.author_session_id != user_id,
        Creation.is_hidden.is_(False),
        Creation.id.notin_(already_liked),
        Creation.id.notin_(already_seen),
    )

    if category:
        query = query.filter(Creation.category == category)

    creation = query.order_by(func.random()).first()

    if not creation:
        return FeedResponse(creation=None, exhausted=True)

    # Отмечаем как показанное — это исключает творение из ленты навсегда
    # (даже если пользователь его не лайкнет, просто пролистает "мимо"),
    # сброса этой истории больше нет.
    db.add(Seen(creation_id=creation.id, viewer_session_id=user_id))
    db.commit()

    return FeedResponse(creation=creation, exhausted=False)
