from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from ..core.dependencies import get_current_user
from ..db.session import get_db
from ..models.user import User
from ..schemas.deck import DeckCreate, DeckResponse, DeckUpdate
from ..services import deck as service

router = APIRouter(prefix="/api/decks", tags=["Decks"])
Database = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("", response_model=DeckResponse, status_code=201)
def create_deck(data: DeckCreate, db: Database, user: CurrentUser):
    return service.create_deck(db, user.user_id, data)


@router.get("", response_model=list[DeckResponse])
def list_decks(db: Database, user: CurrentUser):
    return service.list_decks(db, user.user_id)


@router.get("/{deck_id}", response_model=DeckResponse)
def get_deck(deck_id: int, db: Database, user: CurrentUser):
    return service.get_deck(db, user.user_id, deck_id)


@router.patch("/{deck_id}", response_model=DeckResponse)
def update_deck(deck_id: int, data: DeckUpdate, db: Database, user: CurrentUser):
    return service.update_deck(db, user.user_id, deck_id, data)


@router.delete("/{deck_id}", status_code=204)
def delete_deck(deck_id: int, db: Database, user: CurrentUser):
    service.delete_deck(db, user.user_id, deck_id)
    return Response(status_code=204)
