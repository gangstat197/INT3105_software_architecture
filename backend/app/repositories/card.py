from datetime import datetime

from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session, selectinload

from ..models.card import Card
from ..models.deck import Deck
from ..models.word import Word, WordDefinition, WordMeaning


def word_options():
    definitions = selectinload(Card.word).selectinload(Word.meanings).selectinload(WordMeaning.definitions)
    return (
        definitions.selectinload(WordDefinition.synonyms),
        definitions.selectinload(WordDefinition.antonyms),
    )


def get_by_id(db: Session, card_id: int) -> Card | None:
    return db.scalar(select(Card).where(Card.card_id == card_id).options(*word_options()))


def list_by_deck(db: Session, deck_id: int) -> list[Card]:
    return list(db.scalars(
        select(Card).where(Card.deck_id == deck_id)
        .options(*word_options()).order_by(Card.card_id)
    ))


def create(db: Session, deck_id: int, word_id: int, notes: str | None) -> Card:
    card = Card(deck_id=deck_id, word_id=word_id, notes=notes)
    db.add(card)
    return card


def delete(db: Session, card: Card) -> None:
    db.delete(card)


def due_condition(now: datetime):
    return or_(Card.next_reviewed_date.is_(None), Card.next_reviewed_date <= now)


def list_due(db: Session, user_id: int, now: datetime) -> list[Card]:
    return list(db.scalars(
        select(Card).join(Card.deck)
        .where(Deck.user_id == user_id, due_condition(now))
        .options(*word_options())
        .order_by(Card.next_reviewed_date.asc().nulls_last(), Card.card_id)
        .limit(20)
    ))


def record_review(
    db: Session, card_id: int, user_id: int, expected_version: int,
    is_correct: bool, level: int, now: datetime, next_date: datetime,
) -> bool:
    result = db.execute(
        update(Card).where(
            Card.card_id == card_id,
            Card.deck_id.in_(select(Deck.deck_id).where(Deck.user_id == user_id)),
            Card.review_version == expected_version,
            due_condition(now),
        ).values(
            progress_level=level,
            last_reviewed_at=now,
            next_reviewed_date=next_date,
            review_total_count=Card.review_total_count + 1,
            review_correct_count=Card.review_correct_count + int(is_correct),
            review_version=Card.review_version + 1,
        ).execution_options(synchronize_session=False)
    )
    return result.rowcount == 1
