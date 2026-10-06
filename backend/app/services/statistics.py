from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..repositories import statistics as repository
from ..schemas.statistics import DeckStatisticsResponse



def get_deck_statistics(
        db: Session, user_id: int, deck_id: int
) -> DeckStatisticsResponse:
    deck = repository.get_deck_by_id(db, deck_id)

    if deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")

    if deck.user_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")


    stats = repository.get_deck_card_stats(db, deck_id)

    progress = (
        stats.progressed_cards / stats.total_cards
        if stats.total_cards > 0
        else 0.0
    )

    review_accuracy = (
        stats.review_correct / stats.review_total
        if stats.review_total > 0
        else None
    )


    return DeckStatisticsResponse(
        deck_id = deck.deck_id,
        deck_name = deck.name,
        total_cards = stats.total_cards,
        progress =  progress,
        review_accuracy = review_accuracy,

)
