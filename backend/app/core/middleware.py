from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.app.core.security import decode_access_token


PUBLIC_PATHS = {
    "/",
    "/docs",
    "/docs/oauth2-redirect",
    "/redoc",
    "/openapi.json",
    "/register",
    "/login",
    "/forgot-password",
    "/reset-password"
}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        authorization = request.headers.get("Authorization")

        if not authorization:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing authentication token"}
            )

        if not authorization.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid authentication token"}
            )

        token = authorization[len("Bearer "):]

        payload = decode_access_token(token)

        if payload is None:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid authentication token"}
            )
        
        return await call_next(request)
