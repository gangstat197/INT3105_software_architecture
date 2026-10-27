from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models.card import Card
from ..repositories import card as repository
from ..schemas.card import CardCreate, CardUpdate
from ..schemas.dictionary import WordNotFound
from . import deck as deck_service
from . import dictionary
from .dictionary_provider import DictionaryProviderError


def _commit_card(db: Session, deck_id: int, word_id: int) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if repository.get_by_deck_word(db, deck_id, word_id) is not None:
            raise HTTPException(status_code=409, detail="Word already exists in this deck") from exc
        raise


def get_card(db: Session, user_id: int, card_id: int) -> Card:
    card = repository.get_by_id(db, card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    deck_service.get_deck(db, user_id, card.deck_id)
    return card


def list_cards(db: Session, user_id: int, deck_id: int) -> list[Card]:
    deck_service.get_deck(db, user_id, deck_id)
    return repository.list_by_deck(db, deck_id)


def create_card(db: Session, user_id: int, deck_id: int, data: CardCreate) -> Card:
    deck_service.get_deck(db, user_id, deck_id)
    if not dictionary.normalize_word(data.word):
        raise HTTPException(status_code=422, detail="Word is empty after normalization")
    try:
        result = dictionary.lookup(db, data.word, data.language)
    except DictionaryProviderError as exc:
        raise HTTPException(status_code=502, detail="Dictionary provider unavailable") from exc
    if isinstance(result, WordNotFound):
        raise HTTPException(status_code=404, detail="Word Not Found")
    if repository.get_by_deck_word(db, deck_id, result.word.word_id) is not None:
        raise HTTPException(status_code=409, detail="Word already exists in this deck")
    card = repository.create(db, deck_id, result.word.word_id, data.notes)
    _commit_card(db, deck_id, result.word.word_id)
    db.refresh(card)
    return card


def update_card(db: Session, user_id: int, card_id: int, data: CardUpdate) -> Card:
    card = get_card(db, user_id, card_id)
    if data.deck_id is not None:
        deck_service.get_deck(db, user_id, data.deck_id)
        existing = repository.get_by_deck_word(db, data.deck_id, card.word_id)
        if existing is not None and existing.card_id != card.card_id:
            raise HTTPException(status_code=409, detail="Word already exists in this deck")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(card, field, value)
    _commit_card(db, card.deck_id, card.word_id)
    db.refresh(card)
    return card


def delete_card(db: Session, user_id: int, card_id: int) -> None:
    card = get_card(db, user_id, card_id)
    repository.delete(db, card)
    db.commit()
