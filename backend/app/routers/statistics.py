from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..core.dependencies import get_current_user
from ..db.session import get_db
from ..models.user import User
from ..schemas.statistics import DeckStatisticsResponse
from ..services import statistics as service


router = APIRouter(prefix="/api", tags=["Statistics"])

Database = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get(
    "/decks/{deck_id}/statistics",
    response_model=DeckStatisticsResponse,
)
def get_deck_statistics(
    deck_id: int,
    db: Database,
    user: CurrentUser,
):
    return service.get_deck_statistics(db, user_id=user.user_id, deck_id=deck_id)
