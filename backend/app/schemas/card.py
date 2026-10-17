from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CardCreate(BaseModel):
    word: str = Field(min_length=1, max_length=255)
    language: str = Field(default="en", min_length=1, max_length=10)
    notes: str | None = None

    @field_validator("word", "language", mode="before")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class CardUpdate(BaseModel):
    notes: str | None = None
    deck_id: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_deck_id(self):
        if "deck_id" in self.model_fields_set and self.deck_id is None:
            raise ValueError("deck_id cannot be null")
        return self


class RelatedWordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    word: str


class DefinitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    definition: str
    example: str | None
    synonyms: list[RelatedWordResponse]
    antonyms: list[RelatedWordResponse]


class MeaningResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    part_of_speech: str | None
    ipa: str | None
    audio: str | None
    definitions: list[DefinitionResponse]


class WordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    word_id: int
    word: str
    language: str
    meanings: list[MeaningResponse]


class CardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    card_id: int
    deck_id: int
    word_id: int
    notes: str | None
    word: WordResponse
    progress_level: int
    last_reviewed_at: datetime | None
    next_reviewed_date: datetime | None
    review_total_count: int
    review_correct_count: int
    review_version: int


class ReviewCreate(BaseModel):
    is_correct: bool = Field(strict=True)
    expected_review_version: int = Field(ge=0)
