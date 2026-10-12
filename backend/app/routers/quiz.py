from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..core.dependencies import get_current_user
from ..db.session import get_db
from ..models.user import User
from ..schemas.quiz import (
    AttemptResponse,
    AttemptSubmit,
    AttemptSummary,
    QuizCreate,
    QuizDetailResponse,
    QuizSummary,
    QuizType,
)
from ..services import quiz as service

router = APIRouter(tags=["quizzes"])
Database = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]

@router.post("/api/decks/{deck_id}/quizzes", response_model=QuizDetailResponse, status_code=201)
def create_quiz(deck_id: int, data: QuizCreate, db: Database, user: CurrentUser):
    """Backend picks up to 20 valid cards from the deck and freezes the questions"""
    return service.create_quiz(db, user.user_id, deck_id, data.quiz_type)


@router.get("/api/quizzes", response_model=list[QuizSummary])
def list_quizzes(db: Database, user: CurrentUser, quiz_type: QuizType):
    return service.list_quizzes(db, user.user_id, quiz_type)


@router.get("/api/quizzes/{quiz_id}", response_model=QuizDetailResponse)
def get_quiz(quiz_id: int, db: Database, user: CurrentUser):
    return service.get_quiz(db, user.user_id, quiz_id)


@router.get("/api/quizzes/{quiz_id}/attempts", response_model=list[AttemptSummary])
def list_attempts(quiz_id: int, db: Database, user: CurrentUser):
    return service.list_attempts(db, user.user_id, quiz_id)


@router.post("/api/quizzes/{quiz_id}/attempts", response_model=AttemptResponse, status_code=201)
def start_attempt(quiz_id: int, db: Database, user: CurrentUser):
    return service.start_attempt(db, user.user_id, quiz_id)


@router.get("/api/quizzes/{quiz_id}/attempts/{attempt_id}", response_model=AttemptResponse)
def get_attempt(quiz_id: int, attempt_id: int, db: Database, user: CurrentUser):
    return service.get_attempt(db, user.user_id, quiz_id, attempt_id)


@router.post("/api/quizzes/{quiz_id}/attempts/{attempt_id}/submit", response_model=AttemptResponse)
def submit_attempt(quiz_id: int, attempt_id: int, data: AttemptSubmit, db: Database, user: CurrentUser):
    return service.submit_attempt(db, user.user_id, quiz_id, attempt_id, data)