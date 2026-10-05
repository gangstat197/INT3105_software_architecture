from fastapi import FastAPI

from .routers.auth import router as auth_router
from .routers.deck import router as deck_router

app = FastAPI()
app.include_router(auth_router)
app.include_router(deck_router)


@app.get("/", include_in_schema=False)
def root():
    return {"message": "Flashcards API", "docs": "/docs"}
