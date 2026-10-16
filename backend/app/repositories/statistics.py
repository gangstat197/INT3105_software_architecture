from sqlalchemy import case, func, select
from sqlalchemy.orm import Session


from ..models.card import Card
from ..models.deck import Deck
from ..models.quiz import Attempt, Quiz


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

def get_quiz_by_id(db: Session, quiz_id: int) -> Quiz | None:
    return db.get(Quiz, quiz_id)

def get_completed_attempts(
        db: Session,
        quiz_id: int,
    ) -> list[Attempt]:
    statement = (
        select(Attempt)
        .where(
            Attempt.quiz_id == quiz_id,
            Attempt.completed_at.is_not(None),
        )
        .order_by(
            Attempt.completed_at.desc(),
            Attempt.attempt_id.desc(),
        )
    )
    return list(db.scalars(statement).all())



def count_user_decks(db: Session, user_id: int) -> int:
    statement = select(func.count(Deck.deck_id)).where(
        Deck.user_id == user_id
    )
    return db.execute(statement).scalar_one()


def get_user_card_stats(db: Session, user_id: int):
    statement = (
        select(
            func.count(Card.card_id).label("total_cards"),
            func.coalesce(
                func.sum(case((Card.progress_level >= 2, 1), else_=0)), 0
            ).label("progressed_cards"),
            func.coalesce(func.sum(Card.review_total_count), 0).label("review_total"),
            func.coalesce(func.sum(Card.review_correct_count), 0).label("review_correct"),
        )
        .select_from(Card)
        .join(Deck, Card.deck_id == Deck.deck_id)
        .where(Deck.user_id == user_id)
    )
    return db.execute(statement).one()


def count_user_completed_attempts(db: Session, user_id: int) -> int:
    statement = (
        select(func.count(Attempt.attempt_id))
        .select_from(Attempt)
        .join(Quiz, Attempt.quiz_id == Quiz.quiz_id)
        .join(Deck, Quiz.deck_id == Deck.deck_id)
        .where(
            Deck.user_id == user_id,
            Attempt.completed_at.is_not(None),
        )
    )
    return db.execute(statement).scalar_one()