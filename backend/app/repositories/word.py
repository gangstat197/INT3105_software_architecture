from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Any
from backend.app.models.word import (
    Word,
    WordMeaning,
    WordDefinition,
    WordSynonym,
    WordAntonym,
)


def get_word_by_id(db: Session, word_id: int) -> Word | None:
    return db.scalar(
        select(Word).where(Word.word_id == word_id,)
    )


def get_word_by_normalized_word(
        db: Session, 
        normalized_word: str, 
        language: str = "en"
) -> Word | None:
    return db.scalar(
        select(Word).where(
            Word.language == language,
            Word.normalized_word == normalized_word,
        )
    )


def create_word(
    db: Session,
    word: str,
    normalized_word: str,
    language: str,
    meanings: list[dict[str, Any]],
) -> Word:
    word_model = Word(
        word=word,
        normalized_word=normalized_word,
        language=language,
    )

    for meaning_data in meanings:
        ipa = meaning_data.get("ipa", [])
        audio = meaning_data.get("audio", [])

        meaning = WordMeaning(
            part_of_speech=meaning_data.get("part_of_speech"),
            ipa=ipa[0] if ipa else None,
            audio=audio[0] if audio else None,
        )

        word_model.meanings.append(meaning)

        for definition_data in meaning_data.get("definitions", []):
            examples = definition_data.get("examples", [])

            definition = WordDefinition(
                definition=definition_data["definition"],
                example=examples[0] if examples else None,
            )

            meaning.definitions.append(definition)

            for synonym in definition_data.get("synonyms", []):
                definition.synonyms.append(
                    WordSynonym(word=synonym)
                )

            for antonym in definition_data.get("antonyms", []):
                definition.antonyms.append(
                    WordAntonym(word=antonym)
                )

    db.add(word_model)
    db.flush()

    return word_model