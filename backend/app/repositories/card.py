from datetime import datetime

from sqlalchemy import case, or_, select, update
from sqlalchemy.orm import Session, selectinload

from backend.app.models.card import Card
from backend.app.models.deck import Deck
from backend.app.models.word import Word, WordMeaning, WordDefinition


def get_card_owner(db: Session, card_id: int) -> tuple[Card, int] | None:
    row = db.execute(
        select(Card, Deck.user_id)
        .join(Deck, Deck.deck_id == Card.deck_id)
        .where(Card.card_id == card_id)
    ).first()

    return (row[0], row[1]) if row else None


def list_due_cards(db: Session, user_id: int, now: datetime, limit: int = 20) -> list[Card]:
    stmt = (
        select(Card)
        .join(Deck, Deck.deck_id == Card.deck_id)
        .where(
            Deck.user_id == user_id,
            or_(Card.last_reviewed_at.is_(None), Card.next_reviewed_date <= now),
        )
        .options(
            selectinload(Card.word)
            .selectinload(Word.meanings)
            .selectinload(WordMeaning.definitions)
            .selectinload(WordDefinition.synonyms),
            
            selectinload(Card.word)
            .selectinload(Word.meanings)
            .selectinload(WordMeaning.definitions)
            .selectinload(WordDefinition.antonyms),
        )
        .order_by(
            case((Card.next_reviewed_date.is_(None), 1), else_=0),
            Card.next_reviewed_date.asc(),
            Card.card_id.asc(),
        )
        .limit(min(max(limit, 1), 20))
    )

    return list(db.scalars(stmt).unique().all())


def submit_due_review(
    db: Session,
    card_id: int,
    user_id: int,
    expected_review_version: int,
    is_correct: bool,
    now: datetime,
    next_review_date: datetime,
    new_progress_level: int,
) -> dict | None:
    owns_card = select(Deck.deck_id).where(
        Deck.deck_id == Card.deck_id,
        Deck.user_id == user_id,
    ).exists()

    due = or_(Card.last_reviewed_at.is_(None), Card.next_reviewed_date <= now)
    
    stmt = (
        update(Card)
        .where(
            Card.card_id == card_id,
            owns_card,
            Card.review_version == expected_review_version,
            due,
        )
        .values(
            progress_level=new_progress_level,
            last_reviewed_at=now,
            next_reviewed_date=next_review_date,
            review_version=Card.review_version + 1,
            review_total_count=Card.review_total_count + 1,
            review_correct_count=Card.review_correct_count + (1 if is_correct else 0),
        )
        .returning(
            Card.card_id,
            Card.progress_level,
            Card.next_reviewed_date,
            Card.review_version,
        )
    )

    row = db.execute(stmt).mappings().one_or_none()

    if row is None:
        return None
    
    return {
        "card_id": row["card_id"],
        "new_progress_level": row["progress_level"],
        "next_review_date": row["next_reviewed_date"],
        "review_version": row["review_version"],
    }
