from typing import Literal

from pydantic import BaseModel


class DatabaseHealth(BaseModel):
    status: Literal["ok"] = "ok"
    database: Literal["connected"] = "connected"


class ModelInfo(BaseModel):
    name: str
    table: str
    relationships: dict[str, str]


class ModelHealth(BaseModel):
    status: Literal["ok"] = "ok"
    model_count: int
    models: list[ModelInfo]
