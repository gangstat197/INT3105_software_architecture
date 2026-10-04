from fastapi import FastAPI

from .routers.health import router as health_router
from .routers.deck import router as deck_router

app = FastAPI()
app.include_router(health_router)
app.include_router(deck_router)
