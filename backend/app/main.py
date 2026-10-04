from fastapi import FastAPI

from .core.middleware import AuthMiddleware
from .routers.health import router as health_router
from .routers.deck import router as deck_router

app = FastAPI()
app.include_router(health_router)
app.include_router(deck_router)
app.add_middleware(AuthMiddleware)
