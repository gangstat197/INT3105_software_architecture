from dataclasses import dataclass
from typing import Literal
from backend.app.models.word import Word


@dataclass
class WordFound:
    status: Literal["found"]
    word: Word


@dataclass
class WordNotFound:
    status: Literal["not_found"]

    
WordLookupResult = WordFound | WordNotFound