from app.models.base import Base
from app.models.deck import Deck
from typing import Optional, List 
from datetime import datetime
from sqlalchemy import DateTime, Boolean, Text, ForeignKey, ForeignKeyConstraint, UniqueConstraint, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

class Quiz(Base):
    __tablename__ = "quiz"
    quiz_id: Mapped[int] = mapped_column(primary_key=True)
    deck_id: Mapped[int] = mapped_column(ForeignKey("deck.deck_id", ondelete="CASCADE"))

    deck: Mapped["Deck"] = relationship(back_populates="quizzes")
    quiz_type: Mapped[str] = mapped_column()

    quiz_questions: Mapped[List["QuizQuestion"]] = relationship(
        back_populates="quiz", cascade="all, delete-orphan"
    )

    attempts: Mapped[List["Attempt"]] = relationship(
        back_populates="quiz", cascade="all, delete-orphan"
    )

class QuizQuestion(Base):
    __tablename__ = "quiz_question"
    __table_args__ = (
        PrimaryKeyConstraint("quiz_id", "card_id", name="quiz_question_pk"), # composite PK 
    )

    quiz_id: Mapped[int] = mapped_column(ForeignKey("quiz.quiz_id", ondelete="CASCADE"))
    card_id: Mapped[int] = mapped_column()

    prompt_snapshot: Mapped[str] = mapped_column(Text)
    answer_snapshot: Mapped[str] = mapped_column(Text)
    options_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB)

    quiz: Mapped["Quiz"] = relationship(back_populates="quiz_questions")

class QuizCard(Base):
    __tablename__ = "quiz_card"
    # Composite FK
    # https://docs.sqlalchemy.org/en/21/core/constraints.html#sqlalchemy.schema.ForeignKeyConstraint
    __table_args__ = (
        PrimaryKeyConstraint(
            "quiz_id", 
            "attempt_id", 
            "card_id", 
            name="quiz_card_pk"
        ),
        ForeignKeyConstraint(
            ["attempt_id", "quiz_id"],
            ["attempt.attempt_id", "attempt.quiz_id"], # Composite FK needs to point to a singular table
            ondelete="CASCADE",
            name="fk_quiz_card_attempt"
        ),
        ForeignKeyConstraint(
            ["quiz_id", "card_id"],
            ["quiz_question.quiz_id", "quiz_question.card_id"],
            ondelete="CASCADE",
            name="fk_quiz_card_question",
        ),
    )

    quiz_id: Mapped[int] = mapped_column()
    attempt_id: Mapped[int] = mapped_column()
    card_id: Mapped[int] = mapped_column()

    user_answer: Mapped[Optional[str]] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean)

    attempt: Mapped["Attempt"] = relationship(back_populates="quiz_cards")

class Attempt(Base):
    __tablename__ = "attempt"
    __table_args__ = (
        UniqueConstraint("attempt_id", "quiz_id", name="unique_constraint_attempt_quiz_id"),
    )

    attempt_id: Mapped[int] = mapped_column(primary_key=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quiz.quiz_id", ondelete="CASCADE"))
    score: Mapped[Optional[int]] = mapped_column()
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    quiz: Mapped["Quiz"] = relationship(back_populates="attempts")

    quiz_cards: Mapped[List["QuizCard"]] = relationship(
        back_populates="attempt"
    )