import random
import re
from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from ..models.quiz import (
    Attempt,
    Quiz,
    QuizCard,
    QuizQuestion
)
from ..schemas.quiz import (
    QuizCreate
)

from fastapi import HTTPException
from . import deck as deck_service
from ..repositories import quiz as repository

OPTION_IDS = ("A", "B", "C", "D")


def blank_word(example: str, word: str):
    """Replace whole-word matches of `word` with a blank, or None if the word isn't in the example."""
    pattern = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
    prompt, count = pattern.subn("_____", example)
    return prompt if count else None


def build_options(answer: str, distractors: list[str]) -> tuple[list[dict], str] | None:
    """Shuffle the answer with 3 distinct distractors once; returns (options, correct option id)."""
    seen = {answer.casefold()}
    picked = []
    for word in distractors:
        if word.casefold() not in seen:
            seen.add(word.casefold())
            picked.append(word)
        if len(picked) == 3:
            break
    if len(picked) < 3:
        return None

    words = [answer, *picked]
    random.shuffle(words)
    options = [{"id": option_id, "text": text} for option_id, text in zip(OPTION_IDS, words)]
    return options, OPTION_IDS[words.index(answer)]


def create_quiz(db: Session, user_id: int, deck_id: int, quiz_type: QuizCreate):
    deck_service.get_deck(db, user_id, deck_id)  # 404 / 403

    examples_by_card = defaultdict(list)
    for card_id, word_id, word, language, example in repository.list_card_examples(db, deck_id):
        prompt = blank_word(example, word)
        if prompt is not None:
            examples_by_card[card_id].append((word_id, word, language, prompt))

    card_ids = list(examples_by_card)
    random.shuffle(card_ids)

    questions = []
    for card_id in card_ids:
        if len(questions) == 20:
            break
        word_id, word, language, prompt = random.choice(examples_by_card[card_id])

        if quiz_type == "fill_blank":
            answer, options = word, None
        else:
            built = build_options(word, repository.list_distractor_words(db, word_id, word, language))
            if built is None:
                continue  # not enough distractors, card isn't valid for multiple choice
            options, answer = built

        questions.append(QuizQuestion(
            card_id=card_id,
            prompt_snapshot=prompt,
            answer_snapshot=answer,
            options_snapshot=options,
        ))

    if not questions:
        raise HTTPException(status_code=400, detail=f"No cards in this deck are usable for a {quiz_type} quiz")

    quiz = repository.create(db, deck_id, quiz_type, questions)
    db.commit()
    db.refresh(quiz)
    return quiz


def list_quizzes(db: Session, user_id: int, quiz_type: str | None) -> list[Quiz]:
    return repository.list_by_user(db, user_id, quiz_type)


def get_quiz(db: Session, user_id: int, quiz_id: int):
    quiz = repository.get_quiz_by_id(db, quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="Quiz not found")
    if quiz.deck.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not the quiz owner")
    return