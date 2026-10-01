"""Register all models so SQLAlchemy can resolve relationship names."""

from .base import Base
from .user import User, PasswordResetToken
from .word import Word, WordMeaning, WordDefinition, WordSynonym, WordAntonym
from .deck import Deck
from .card import Card
from .quiz import Quiz, QuizQuestion, QuizCard, Attempt

__all__ = [
    "Base",
    "User",
    "PasswordResetToken",
    "Word",
    "WordMeaning",
    "WordDefinition",
    "WordSynonym",
    "WordAntonym",
    "Deck",
    "Card",
    "Quiz",
    "QuizQuestion",
    "QuizCard",
    "Attempt",
]
