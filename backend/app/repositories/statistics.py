from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from ..models.card import Card
from ..models.deck import Deck


def get_deck_by_id(db: Session, deck_id: int) -> Deck | None:
    return db.get(Deck, deck_id)


def get_deck_card_stats(db: Session, deck_id: int):
    return db.execute(
        select(
            func.count(Card.card_id).label("total_cards"),
            func.coalesce(
                func.sum(
                    case(
                        (Card.progress_level >= 2, 1),
                        else_=0,
                    )
                ),
                0,
            ).label("progressed_cards"),
            func.coalesce(func.sum(Card.review_total_count), 0).label("review_total"),
            func.coalesce(func.sum(Card.review_correct_count), 0).label("review_correct"),
        ).where(Card.deck_id == deck_id)
    ).one()