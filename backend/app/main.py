from fastapi import FastAPI

from .core.middleware import AuthMiddleware
from .routers.deck import router as deck_router

app = FastAPI()
app.include_router(deck_router)
app.add_middleware(AuthMiddleware)


@app.get("/", include_in_schema=False)
def root():
    return {"message": "Flashcards API", "docs": "/docs"}
