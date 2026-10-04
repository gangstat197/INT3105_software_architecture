from pydantic import BaseModel 
from typing import Optional, List

class DeckCreate(BaseModel):
    name: str 
    description: str

class DeckUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

class DeckResponse(BaseModel):
    deck_id: int 
    name: str 
    description: str 

class DeckListResponse(BaseModel): 
    deck_lists: List[DeckResponse]
