from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..core.config import settings
from ..models.card import Card
from ..repositories import card as repository
from ..schemas.card import ReviewCreate
from .card import get_card


def list_due_cards(db: Session, user_id: int) -> list[Card]:
    return repository.list_due(db, user_id, datetime.now(timezone.utc))


def review_card(db: Session, user_id: int, card_id: int, data: ReviewCreate) -> Card:
    card = get_card(db, user_id, card_id)
    now = datetime.now(timezone.utc)
    level = min(card.progress_level + 1, settings.LEITNER_BOX_COUNT) if data.is_correct else 1
    next_date = now + timedelta(days=settings.LEITNER_INTERVALS[level - 1])
    updated = repository.record_review(
        db, card_id, user_id, data.expected_review_version,
        data.is_correct, level, now, next_date,
    )
    if not updated:
        db.rollback()
        raise HTTPException(status_code=409, detail="Review version changed or card is not due")
    db.commit()
    db.refresh(card)
    return card
