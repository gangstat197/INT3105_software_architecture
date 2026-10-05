from __future__ import annotations
from typing import Any
from urllib.parse import quote
import httpx


DICTIONARY_API_URL = "https://freedictionaryapi.com/api/v1/entries"


class DictionaryProviderError(Exception):
    """Base exception for dictionary provider errors."""


def lookup_provider(word: str, language: str="en", timeout: float=5.0) -> dict[str, Any] | None:
    safe_language = quote(language, safe="")
    safe_word = quote(word, safe="")

    url = f"{DICTIONARY_API_URL}/{safe_language}/{safe_word}"

    try:
        response = httpx.get(url, timeout=timeout)
        response.raise_for_status()

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return None

        raise DictionaryProviderError(
            f"Dictionary provider returned HTTP {exc.response.status_code}"
        ) from exc

    except httpx.RequestError as exc:
        raise DictionaryProviderError(
            "Failed to contact dictionary provider"
        ) from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise DictionaryProviderError(
            "Invalid JSON response from dictionary provider"
        ) from exc

    if not data or (isinstance(data, dict) and not data.get("entries")):
        return None
        
    return data


def parse(data: dict[str, Any]) -> tuple[str, list[dict]]:
    provider_word = data.get("word")

    if not provider_word:
        raise DictionaryProviderError("Dictionary response does not contain a word")

    entries = data.get("entries")

    if not isinstance(entries, list):
        raise DictionaryProviderError("Dictionary response does not contain entries")

    meanings: list[dict] = []

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        part_of_speech = entry.get("partOfSpeech")
        
        pronunciation = extract_pronunciation(entry.get("pronunciations"))
        definitions = extract_definitions(entry.get("senses"))

        if not definitions:
            continue

        meanings.append(
            {
                "part_of_speech": part_of_speech,
                "ipa": pronunciation.get("ipa"),
                "audio": pronunciation.get("audio"),
                "definitions": definitions,
            }
        )

    if not meanings:
        raise DictionaryProviderError("Dictionary entry contains no definitions")

    return provider_word, meanings


def extract_pronunciation(pronunciations: Any) -> dict[str, str | None]:
    if not isinstance(pronunciations, list):
        return {
            "ipa": [], 
            "audio": []
        }

    ipa_list: list[str] = []
    audio_list: list[str] = []

    for pronunciation in pronunciations:
        if not isinstance(pronunciation, dict):
            continue
        if pronunciation.get("text"):
            ipa_list.append(pronunciation["text"])
        if pronunciation.get("audio"):
            audio_list.append(pronunciation["audio"])

    return {"ipa": ipa_list, "audio": audio_list}


def extract_definitions(definitions: Any) -> list[dict]:
    if not isinstance(definitions, list):
        return []

    result: list[dict] = []

    for definition_data in definitions:
        if not isinstance(definition_data, dict):
            continue

        definition = definition_data.get("definition")

        if not definition:
            continue

        example_list = []
        examples = definition_data.get("examples", [])

        if isinstance(examples, list):
            for ex in examples:
                if isinstance(ex, str):
                    example_list.append(ex)
                elif isinstance(ex, dict) and ex.get("text"):
                    example_list.append(ex["text"])

        synonyms = extract_related_words(definition_data.get("synonyms"))
        antonyms = extract_related_words(definition_data.get("antonyms"))

        result.append(
            {
                "definition": definition,
                "examples": example_list,
                "synonyms": synonyms,
                "antonyms": antonyms,
            }
        )

    return result


def extract_related_words(values: Any) -> list[str]:
        if not isinstance(values, list):
            return []

        result: list[str] = []

        for value in values:
            if isinstance(value, str):
                result.append(value)
            elif isinstance(value, dict):
                text = value.get("text")
                if text:
                    result.append(text)

        return result