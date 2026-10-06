from types import SimpleNamespace
from unittest.mock import Mock

from fastapi.testclient import TestClient

from backend.app.core.dependencies import get_current_user
from backend.app.db.session import get_db
from backend.app.main import app
from backend.app.repositories import statistics as repository


def test_deck_statistics_route(monkeypatch):
    deck_lookup = Mock(return_value=SimpleNamespace(
        deck_id=17, user_id=3, name="Vocabulary"
    ))
    monkeypatch.setattr(repository, "get_deck_by_id", deck_lookup)
    monkeypatch.setattr(repository, "get_deck_card_stats", Mock(
        return_value=SimpleNamespace(
            total_cards=4, progressed_cards=2, review_total=10, review_correct=7
        )
    ))
    db = object()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(user_id=3)
    try:
        with TestClient(app) as client:
            response = client.get("/api/decks/17/statistics")
        assert response.status_code == 200
        assert response.json() == {
            "deck_id": 17,
            "deck_name": "Vocabulary",
            "total_cards": 4,
            "progress": 0.5,
            "review_accuracy": 0.7,
        }
        deck_lookup.assert_called_once_with(db, 17)
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
