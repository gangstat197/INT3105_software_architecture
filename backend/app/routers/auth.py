from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
)
from ..services import auth as auth_service

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=RegisterResponse)
def register(
    request: RegisterRequest,
    db: Annotated[Session, Depends(get_db)],
) -> RegisterResponse:
    return auth_service.register(db, request)


@router.post("/login", response_model=LoginResponse)
def login(
    request: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> LoginResponse:
    return auth_service.login(db, request)


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(
    request: ForgotPasswordRequest,
    db: Annotated[Session, Depends(get_db)],
) -> MessageResponse:
    return auth_service.forgot_password(db, request)


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(
    request: ResetPasswordRequest,
    db: Annotated[Session, Depends(get_db)],
) -> MessageResponse:
    return auth_service.reset_password(db, request)
