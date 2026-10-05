from backend.app.schemas.dictionary import *
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from dictionary_provider import lookup_provider, parse
from backend.app.repositories.word import get_word_by_normalized_word, create_word
import unicodedata
import string


def normalize_word(word: str) -> str:
    word = word.lower().strip()
    word = word.strip(string.punctuation)
    word = unicodedata.normalize("NFKD", word).encode("ascii", "ignore").decode("utf-8")
    
    return word


def lookup(db: Session, word: str, language: str) -> WordLookupResult:
    normalized_word = normalize_word(word)

    existing_word = get_word_by_normalized_word(db, normalized_word, language)

    if existing_word:
        return existing_word

    data = lookup_provider(
        word=word, 
        language=language,
    )

    if data is None:
        return WordNotFound()

    provider_word, meanings = parse(data)

    word_model = create_word(
        db=db,
        word=provider_word,
        normalized_word=normalized_word,
        language=language,
        meanings=meanings,
    )

    db.commit()

    return WordFound(word=word_model)