from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models.card import Card
from ..models.deck import Deck
from ..models.quiz import Attempt, Quiz, QuizQuestion, QuizCard
from ..models.word import Word, WordDefinition, WordMeaning, WordSynonym

def list_card_examples(db: Session, deck_id: int):
    """Every (card, word, example) row in the deck whose example mentions the word."""
    stmt = (
        select(Card.card_id, Word.word_id, Word.word, Word.language, WordDefinition.example)
        .join(Word, Card.word_id == Word.word_id)
        .join(WordMeaning, WordMeaning.word_id == Word.word_id)
        .join(WordDefinition, WordDefinition.word_meaning_id == WordMeaning.word_meaning_id)
        .where(
            Card.deck_id == deck_id,
            WordDefinition.example.ilike(func.concat("%", Word.word, "%")),
        )
    )
    return db.execute(stmt).all()


def list_distractor_words(db: Session, word_id: int, word: str, language: str, limit: int = 10) -> list[str]:
    """Random words of the same language that are neither the target word nor its synonyms."""
    synonyms = (
        select(func.lower(WordSynonym.word))
        .join(WordDefinition, WordSynonym.word_definition_id == WordDefinition.word_definition_id)
        .join(WordMeaning, WordDefinition.word_meaning_id == WordMeaning.word_meaning_id)
        .where(WordMeaning.word_id == word_id)
    )
    stmt = (
        select(Word.word)
        .where(
            Word.word_id != word_id,
            Word.language == language,
            func.lower(Word.word) != word.lower(),
            func.lower(Word.word).not_in(synonyms),
        )
        .order_by(func.random())
        .limit(limit)
    )
    return list(db.scalars(stmt))


def create(db: Session, deck_id: int, quiz_type: str, questions: list[QuizQuestion]) -> Quiz:
    quiz = Quiz(deck_id=deck_id, quiz_type=quiz_type, quiz_questions=questions)
    db.add(quiz)
    return quiz


def list_by_user(db: Session, user_id: int, quiz_type: str | None):
    stmt = (
        select(Quiz)
        .join(Deck, Quiz.deck_id == Deck.deck_id)
        .where(Deck.user_id == user_id)
    )

    if quiz_type is not None:
        stmt = stmt.where(Quiz.quiz_type == quiz_type)
    return list(db.scalars(statement=stmt.order_by(Quiz.quiz_id)))

def get_quiz_by_id(db: Session, quiz_id: int) -> Quiz | None:
    return db.get(Quiz, quiz_id)

def get_attempt_by_id(db: Session, quiz_id:int, attempt_id: int, for_update: bool = False) -> Attempt | None:
    stmt = select(Attempt).where(Attempt.attempt_id == attempt_id, Attempt.quiz_id == quiz_id)
    if for_update:
        # row lock so two concurrent submits can't both see completed_at is null
        # if user double clicks submit
        stmt = stmt.with_for_update().execution_options(populate_existing=True)
    return db.scalars(stmt).first()
    
def list_attempt(db: Session, quiz_id: int):
    stmt = (
        select(Attempt)
        .where(Attempt.quiz_id == quiz_id)
        .order_by(Attempt.attempt_id)
    )
    return list(db.scalars(statement=stmt))

def create_attempt(db: Session, quiz_id: int, started_at: datetime) -> Attempt:
    attempt = Attempt(quiz_id=quiz_id, started_at=started_at)
    db.add(attempt)
    return attempt

def add_answer(db: Session, answers: list[QuizCard]):
    db.add_all(answers)