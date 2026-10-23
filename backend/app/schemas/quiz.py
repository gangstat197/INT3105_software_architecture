from pydantic import BaseModel, ConfigDict
from typing import Literal
from typing import List
from datetime import datetime

QuizType = Literal["multiple_choice", "fill_blank"]

class QuizCreate(BaseModel):
    """Ensure quiz type can only be of 2 types"""
    quiz_type: QuizType

class QuizOptionSnapshot(BaseModel):
    """One option in multiple choice"""
    id: Literal["A", "B", "C", "D"] # answers user can choose
    text: str # the word itself

class QuizQuestionPublic(BaseModel):
    """
    Public quiz question so we don't send answer before the user submits
    so there's no answer_snapshot field like in DB model
    """
    model_config = ConfigDict(from_attributes=True)
    card_id: int
    prompt_snapshot: str # the question
    options_snapshot: List[QuizOptionSnapshot] | None # the answer, fill in the blank doesn't have ABCD so None

class QuizViewSummary(BaseModel):
    """
    In list view, users can view all quizzes
    """
    model_config = ConfigDict(from_attributes=True)
    quiz_id: int
    deck_id: int
    quiz_type: QuizType

class QuizDetailResponse(QuizViewSummary):
    """One quiz with its questions (no answers), for viewing or taking it"""
    model_config = ConfigDict(from_attributes=True)

    quiz_questions: List[QuizQuestionPublic]

class QuestionResult(BaseModel):
    """A question the user got wrong, revealed only after submit"""
    card_id: int
    prompt_snapshot: str
    options_snapshot: list[QuizOptionSnapshot] | None
    user_answer: str | None
    correct_answer: str
    
class AttemptSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    attempt_id: int
    quiz_id: int
    score: int | None
    started_at: datetime
    completed_at: datetime | None

class AttemptResponse(AttemptSummary):
    total_questions: int
    questions: List[QuizQuestionPublic] | None = None
    wrong_questions: List[QuestionResult] | None = None

class AttemptSubmit(AttemptSummary):
    pass