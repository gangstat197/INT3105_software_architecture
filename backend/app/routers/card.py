from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from ..core.dependencies import get_current_user
from ..db.session import get_db
from ..models.user import User
from ..schemas.card import CardCreate, CardResponse, CardUpdate
from ..services import card as service

router = APIRouter(prefix="/api", tags=["Cards"])
Database = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("/decks/{deck_id}/cards", response_model=CardResponse, status_code=201)
def create_card(deck_id: int, data: CardCreate, db: Database, user: CurrentUser):
    return service.create_card(db, user.user_id, deck_id, data)


@router.get("/decks/{deck_id}/cards", response_model=list[CardResponse])
def list_cards(deck_id: int, db: Database, user: CurrentUser):
    return service.list_cards(db, user.user_id, deck_id)


@router.patch("/cards/{card_id}", response_model=CardResponse)
def update_card(card_id: int, data: CardUpdate, db: Database, user: CurrentUser):
    return service.update_card(db, user.user_id, card_id, data)


@router.delete("/cards/{card_id}", status_code=204)
def delete_card(card_id: int, db: Database, user: CurrentUser):
    service.delete_card(db, user.user_id, card_id)
    return Response(status_code=204)
