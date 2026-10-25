from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.core.security import create_access_token
from backend.app.db.session import get_db
from backend.app.main import app
from backend.app.models import Base, Card, Deck, Quiz, QuizQuestion, User, Word
from backend.app.services import dictionary
from backend.app.services.dictionary_provider import DictionaryProviderError


# SQLite is used only in tests; the production model stays PostgreSQL JSONB.
@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kwargs):
    return "JSON"


@pytest.fixture
def api(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, record):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add_all([
            User(user_id=1, username="owner", email="owner@test.com", password_hash="unused"),
            User(user_id=2, username="other", email="other@test.com", password_hash="unused"),
        ])
        db.flush()
        db.add_all([
            Deck(deck_id=1, user_id=1, name="First"),
            Deck(deck_id=2, user_id=1, name="Second"),
            Deck(deck_id=3, user_id=2, name="Private"),
        ])
        db.commit()

        def override_db():
            try:
                yield db
            finally:
                db.rollback()

        app.dependency_overrides[get_db] = override_db
        monkeypatch.setattr(dictionary, "lookup_provider", lambda **kwargs: {
            "word": kwargs["word"],
            "entries": [{
                "partOfSpeech": "noun",
                "pronunciations": [{"text": "/test/", "audio": "https://example.com/audio.mp3"}],
                "senses": [{"definition": "A test word", "examples": ["A test example"],
                            "synonyms": ["sample"], "antonyms": ["opposite"]}],
            }],
        })
        with TestClient(app) as client:
            client.headers["Authorization"] = f"Bearer {create_access_token(1)}"
            yield client, db
        app.dependency_overrides.clear()
    engine.dispose()


def create_card(client, **data):
    response = client.post("/api/decks/1/cards", json={"word": "test", **data})
    assert response.status_code == 201, response.text
    return response.json()


def test_card_crud_and_dictionary_cache(api, monkeypatch):
    client, db = api
    card = create_card(client, word=" Test ", notes="remember")
    assert card["progress_level"] == 1
    assert card["next_reviewed_date"] is None
    assert card["review_version"] == card["review_total_count"] == card["review_correct_count"] == 0
    meaning = card["word"]["meanings"][0]
    assert meaning["ipa"] == "/test/"
    assert meaning["definitions"][0]["synonyms"] == [{"word": "sample"}]
    assert meaning["definitions"][0]["antonyms"] == [{"word": "opposite"}]

    def unexpected_lookup(**kwargs):
        pytest.fail("Cached word must not call the dictionary")

    monkeypatch.setattr(dictionary, "lookup_provider", unexpected_lookup)
    second = create_card(client, word="test")
    assert second["word_id"] == card["word_id"]
    assert len(client.get("/api/decks/1/cards").json()) == 2
    path = f'/api/cards/{card["card_id"]}'
    response = client.patch(path, json={"notes": None, "deck_id": 2})
    assert response.status_code == 200
    assert response.json()["notes"] is None
    assert response.json()["deck_id"] == 2
    assert len(client.get("/api/decks/1/cards").json()) == 1
    assert client.delete(path).status_code == 204
    assert db.get(Word, card["word_id"]) is not None
    assert client.delete(path).status_code == 404


def test_ownership_missing_resources_and_auth(api):
    client, _ = api
    card = create_card(client)
    path = f'/api/cards/{card["card_id"]}'
    for method, url, body in [
        ("get", "/api/decks/3/cards", None),
        ("post", "/api/decks/3/cards", {"word": "test"}),
        ("patch", path, {"deck_id": 3}),
    ]:
        assert client.request(method, url, json=body).status_code == 403
    assert client.get("/api/decks/999/cards").status_code == 404
    assert client.patch(path, json={"deck_id": 999}).status_code == 404
    assert client.patch("/api/cards/999", json={"notes": "x"}).status_code == 404
    assert client.post("/api/reviews/999", json={"is_correct": True, "expected_review_version": 0}).status_code == 404
    client.headers["Authorization"] = f"Bearer {create_access_token(2)}"
    assert client.patch(path, json={"notes": "x"}).status_code == 403
    assert client.delete(path).status_code == 403
    assert client.post(f'/api/reviews/{card["card_id"]}', json={"is_correct": True, "expected_review_version": 0}).status_code == 403
    assert client.get("/api/reviews/due").json() == []
    client.headers.pop("Authorization")
    for method, url, body in [
        ("get", "/api/decks/1/cards", None),
        ("post", "/api/decks/1/cards", {"word": "test"}),
        ("patch", path, {"notes": "x"}),
        ("delete", path, None),
        ("get", "/api/reviews/due", None),
        ("post", f'/api/reviews/{card["card_id"]}', {"is_correct": True, "expected_review_version": 0}),
    ]:
        assert client.request(method, url, json=body).status_code == 401


def test_dictionary_errors_and_validation(api, monkeypatch):
    client, db = api
    for word in ["", "   ", "!!!"]:
        assert client.post("/api/decks/1/cards", json={"word": word}).status_code == 422
    monkeypatch.setattr(dictionary, "lookup_provider", lambda **kwargs: None)
    assert client.post("/api/decks/1/cards", json={"word": "missing"}).status_code == 404
    assert db.scalars(select(Card)).all() == []
    assert db.scalars(select(Word)).all() == []

    def unavailable(**kwargs):
        raise DictionaryProviderError("offline")

    monkeypatch.setattr(dictionary, "lookup_provider", unavailable)
    assert client.post("/api/decks/1/cards", json={"word": "test"}).status_code == 502


def test_patch_null_and_preserve_fields(api):
    client, _ = api
    card = create_card(client, notes="keep")
    path = f'/api/cards/{card["card_id"]}'
    assert client.patch(path, json={"deck_id": None}).status_code == 422
    assert client.patch(path, json={"deck_id": 0}).status_code == 422
    response = client.patch(path, json={"deck_id": 2})
    assert response.json()["notes"] == "keep"
    assert response.json()["review_version"] == 0


@pytest.mark.parametrize("level,is_correct,new_level,days", [
    (1, True, 2, 3), (2, True, 3, 7), (3, True, 4, 14),
    (4, True, 5, 30), (5, True, 5, 30), (5, False, 1, 1),
])
def test_leitner_intervals_and_duplicate_requests(api, level, is_correct, new_level, days):
    client, db = api
    data = create_card(client)
    card = db.get(Card, data["card_id"])
    card.progress_level = level
    db.commit()
    path = f'/api/reviews/{card.card_id}'
    body = {"is_correct": is_correct, "expected_review_version": 0}
    assert client.post(path, json={**body, "expected_review_version": 99}).status_code == 409
    response = client.post(path, json=body)
    assert response.status_code == 200, response.text
    reviewed = response.json()
    assert reviewed["progress_level"] == new_level
    assert reviewed["review_version"] == reviewed["review_total_count"] == 1
    assert reviewed["review_correct_count"] == int(is_correct)
    assert (datetime.fromisoformat(reviewed["next_reviewed_date"]) -
            datetime.fromisoformat(reviewed["last_reviewed_at"])) == timedelta(days=days)
    assert client.post(path, json=body).status_code == 409
    assert client.post(path, json={**body, "expected_review_version": 1}).status_code == 409
    db.refresh(card)
    assert card.review_total_count == card.review_version == 1
    assert client.get("/api/reviews/due").json() == []
    card.next_reviewed_date = datetime.now(timezone.utc) - timedelta(days=1)
    db.commit()
    assert client.post(path, json={**body, "expected_review_version": 1}).json()["review_total_count"] == 2


def test_due_order_limit_and_owner(api):
    client, db = api
    data = create_card(client)
    now = datetime.now(timezone.utc)
    overdue = Card(deck_id=1, word_id=data["word_id"], next_reviewed_date=now - timedelta(days=2))
    newer = Card(deck_id=2, word_id=data["word_id"], next_reviewed_date=now - timedelta(days=1))
    db.add_all([overdue, newer,
                Card(deck_id=1, word_id=data["word_id"], next_reviewed_date=now + timedelta(days=1)),
                Card(deck_id=3, word_id=data["word_id"], next_reviewed_date=now - timedelta(days=3))])
    db.add_all([Card(deck_id=1, word_id=data["word_id"]) for _ in range(25)])
    db.commit()
    cards = client.get("/api/reviews/due").json()
    assert len(cards) == 20
    assert [card["card_id"] for card in cards[:3]] == [overdue.card_id, newer.card_id, data["card_id"]]
    assert all(card["deck_id"] in (1, 2) for card in cards)


def test_delete_card_keeps_quiz_snapshot(api):
    client, db = api
    card = create_card(client)
    quiz = Quiz(deck_id=1, quiz_type="fill_blank")
    db.add(quiz)
    db.flush()
    question = QuizQuestion(quiz_id=quiz.quiz_id, card_id=card["card_id"],
                            prompt_snapshot="A ___ example", answer_snapshot="test")
    db.add(question)
    db.commit()
    assert client.delete(f'/api/cards/{card["card_id"]}').status_code == 204
    assert db.get(QuizQuestion, (quiz.quiz_id, card["card_id"])).answer_snapshot == "test"


def test_failed_card_insert_keeps_dictionary_cache(api):
    client, db = api

    def fail_insert(mapper, connection, target):
        raise RuntimeError("Simulated card insert failure")

    event.listen(Card, "before_insert", fail_insert)
    try:
        with pytest.raises(RuntimeError, match="Simulated card insert failure"):
            client.post("/api/decks/1/cards", json={"word": "test"})
    finally:
        event.remove(Card, "before_insert", fail_insert)
    # Dictionary lookup commits its shared cache independently of the card insert.
    cached_word = db.scalar(select(Word))
    assert cached_word is not None
    assert cached_word.normalized_word == "test"
    assert db.scalars(select(Card)).all() == []
    assert create_card(client)["word_id"] == cached_word.word_id


def test_review_validation(api):
    client, _ = api
    card = create_card(client)
    path = f'/api/reviews/{card["card_id"]}'
    assert client.post(path, json={"is_correct": "true", "expected_review_version": 0}).status_code == 422
    assert client.post(path, json={"is_correct": True, "expected_review_version": -1}).status_code == 422
