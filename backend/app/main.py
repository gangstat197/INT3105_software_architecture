from fastapi import FastAPI

from .routers.health import router as health_router
from .core.middleware import AuthMiddleware

app = FastAPI()
app.include_router(health_router)
app.add_middleware(AuthMiddleware)
