from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import timezone

from ..repositories import statistics as repository
from ..schemas.statistics import DeckStatisticsResponse
from ..schemas.statistics import QuizAttemptStatistics, QuizStatisticsResponse
from ..schemas.statistics import UserStatisticsResponse


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


def get_quiz_statistics(
    db: Session, user_id: int, quiz_id: int
) -> QuizStatisticsResponse:
    quiz = repository.get_quiz_by_id(db, quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="Quiz not found")

    deck = repository.get_deck_by_id(db, quiz.deck_id)
    if deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    if deck.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not the quiz owner")

    attempts = repository.get_completed_attempts(db, quiz_id)

    scores = []
    attempt_responses = []

    for attempt in attempts:
        if attempt.score is None:
            raise HTTPException(
                status_code=500,
                detail="Completed attempt is missing a score",
            )

        scores.append(attempt.score)
        attempt_responses.append(
            QuizAttemptStatistics(
                score=attempt.score,
                completed_at=attempt.completed_at.astimezone(timezone.utc),
            )
        )

    return QuizStatisticsResponse(
        quiz_id=quiz.quiz_id,
        quiz_type=quiz.quiz_type,
        total_attempts=len(attempts),
        average_score=sum(scores) / len(scores) if scores else None,
        best_score=max(scores) if scores else None,
        attempts=attempt_responses,
    )

def get_user_statistics(
    db: Session, user_id: int
) -> UserStatisticsResponse:
    total_decks = repository.count_user_decks(db, user_id)
    stats = repository.get_user_card_stats(db, user_id)
    completed_attempts = repository.count_user_completed_attempts(db, user_id)

    overall_progress = (
        stats.progressed_cards / stats.total_cards
        if stats.total_cards > 0 else 0.0
    )
    overall_review_accuracy = (
        stats.review_correct / stats.review_total
        if stats.review_total > 0 else None
    )

    return UserStatisticsResponse(
        total_decks=total_decks,
        total_cards=stats.total_cards,
        overall_progress=overall_progress,
        overall_review_accuracy=overall_review_accuracy,
        total_quizzes_completed=completed_attempts,
    )