import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models import Base
from backend.app.models.card import Card
from backend.app.models.deck import Deck
from backend.app.models.user import User
from backend.app.models.word import Word
from backend.app.schemas.card import CardCreate, CardUpdate
from backend.app.services import card as service


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(
        engine, tables=[table for table in Base.metadata.sorted_tables
                        if table.name not in {"quiz", "quiz_question", "quiz_card", "attempt"}]
    )
    with Session(engine) as session:
        session.add(User(user_id=1, username="test", email="test@example.com", password_hash="unused"))
        session.add_all([Deck(deck_id=i, user_id=1, name=str(i)) for i in (1, 2)])
        session.add(Word(word_id=1, word="hello", normalized_word="hello", language="en"))
        session.commit()
        yield session
    engine.dispose()


def test_create_rejects_normalized_duplicate_in_same_deck(db):
    first = service.create_card(db, 1, 1, CardCreate(word="hello", notes="original"))
    for word in ("hello", "HELLO", " hello! "):
        with pytest.raises(HTTPException) as error:
            service.create_card(db, 1, 1, CardCreate(word=word))
        assert error.value.status_code == 409
    assert len(service.list_cards(db, 1, 1)) == 1
    assert first.notes == "original"
    assert service.create_card(db, 1, 2, CardCreate(word="hello")).deck_id == 2


def test_move_rejects_duplicate_but_allows_same_deck_update(db):
    first = service.create_card(db, 1, 1, CardCreate(word="hello"))
    second = service.create_card(db, 1, 2, CardCreate(word="hello"))
    with pytest.raises(HTTPException) as error:
        service.update_card(db, 1, second.card_id, CardUpdate(deck_id=1))
    assert error.value.status_code == 409
    assert second.deck_id == 2
    assert service.update_card(db, 1, first.card_id, CardUpdate(deck_id=1, notes="updated")).notes == "updated"


def test_database_rejects_duplicate_and_service_rolls_back(db):
    service.create_card(db, 1, 1, CardCreate(word="hello"))
    db.add(Card(deck_id=1, word_id=1))
    with pytest.raises(HTTPException) as error:
        service._commit_card(db, 1, 1)
    assert error.value.status_code == 409
    assert len(service.list_cards(db, 1, 1)) == 1
    db.add(Card(deck_id=1, word_id=1))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
