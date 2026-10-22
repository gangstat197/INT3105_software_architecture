from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..core.dependencies import get_current_user
from ..db.session import get_db
from ..models.user import User
from ..schemas.card import CardResponse, ReviewCreate
from ..services import review as service

router = APIRouter(prefix="/api/reviews", tags=["Reviews"])
Database = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("/due", response_model=list[CardResponse])
def list_due_cards(db: Database, user: CurrentUser):
    return service.list_due_cards(db, user.user_id)


@router.post("/{card_id}", response_model=CardResponse)
def review_card(card_id: int, data: ReviewCreate, db: Database, user: CurrentUser):
    return service.review_card(db, user.user_id, card_id, data)
