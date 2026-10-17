from datetime import datetime

from pydantic import BaseModel

class DeckStatisticsResponse(BaseModel):
    deck_id: int
    deck_name: str
    total_cards: int
    progress: float
    review_accuracy: float | None



class QuizAttemptStatistics(BaseModel):
    score: int
    completed_at: datetime



class QuizStatisticsResponse(BaseModel):
    quiz_id: int
    quiz_type: str
    total_attempts: int
    average_score: float | None
    best_score: int | None
    attempts: list[QuizAttemptStatistics]



class UserStatisticsResponse(BaseModel):
    total_decks: int
    total_cards: int
    overall_progress: float
    overall_review_accuracy: float | None
    total_quizzes_completed: int




