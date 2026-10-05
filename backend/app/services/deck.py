from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models.deck import Deck
from ..repositories import deck as repository
from ..schemas.deck import DeckCreate, DeckUpdate


def get_deck(db: Session, user_id: int, deck_id: int) -> Deck:
    deck = repository.get_by_id(db, deck_id)
    if deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    if deck.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not the deck owner")
    return deck


def list_decks(db: Session, user_id: int) -> list[Deck]:
    return repository.list_by_user(db, user_id)


def create_deck(db: Session, user_id: int, data: DeckCreate) -> Deck:
    deck = repository.create(db, user_id, data.name, data.description)
    db.commit()
    db.refresh(deck)
    return deck


def update_deck(db: Session, user_id: int, deck_id: int, data: DeckUpdate) -> Deck:
    deck = get_deck(db, user_id, deck_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(deck, field, value)
    db.commit()
    db.refresh(deck)
    return deck


def delete_deck(db: Session, user_id: int, deck_id: int) -> None:
    deck = get_deck(db, user_id, deck_id)
    repository.delete(db, deck)
    db.commit()
