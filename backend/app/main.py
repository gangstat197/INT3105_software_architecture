from fastapi import FastAPI

from .core.middleware import AuthMiddleware
from .routers.auth import router as auth_router
from .routers.health import router as health_router

app = FastAPI()

app.include_router(health_router)
app.include_router(auth_router)

app.add_middleware(AuthMiddleware)
