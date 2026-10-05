from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.deck import Deck


def get_by_id(db: Session, deck_id: int) -> Deck | None:
    return db.get(Deck, deck_id)


def list_by_user(db: Session, user_id: int) -> list[Deck]:
    return list(db.scalars(select(Deck).where(Deck.user_id == user_id).order_by(Deck.deck_id)))


def create(db: Session, user_id: int, name: str, description: str | None) -> Deck:
    deck = Deck(user_id=user_id, name=name, description=description)
    db.add(deck)
    return deck


def delete(db: Session, deck: Deck) -> None:
    db.delete(deck)
