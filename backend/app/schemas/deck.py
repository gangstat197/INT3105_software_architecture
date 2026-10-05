from pydantic import BaseModel, ConfigDict, Field, model_validator


class DeckCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class DeckUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None

    @model_validator(mode="after")
    def validate_name(self):
        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("name cannot be null")
        return self


class DeckResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    deck_id: int
    name: str
    description: str | None
