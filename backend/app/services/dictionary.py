from backend.app.schemas.dictionary import *


# stub
def lookup(word: str, language: str) -> WordLookupResult:
    return WordNotFound(status="not_found")