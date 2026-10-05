import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..core.security import create_access_token, hash_password, verify_password
from ..repositories import password_reset as password_reset_repo
from ..repositories import user as user_repo
from ..schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
)

from ..services.email import send_password_reset_email
import logging 

from resend.exceptions import ResendError

logger = logging.getLogger(__name__)

RESET_TOKEN_EXPIRE_MINUTES = 30

def register(db: Session, request: RegisterRequest) -> RegisterResponse:
    if user_repo.get_user_by_username(db, request.username) is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    if user_repo.get_user_by_email(db, request.email) is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )

    password_hash = hash_password(request.password)

    user = user_repo.create_user(
        db=db,
        username=request.username,
        email=request.email,
        password_hash=password_hash,
    )

    return RegisterResponse(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
    )


def login(db: Session, request: LoginRequest) -> LoginResponse:
    user = user_repo.get_user_by_username(db, request.username)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    access_token = create_access_token(user.user_id)

    return LoginResponse(access_token=access_token)


def forgot_password(
    db: Session,
    request: ForgotPasswordRequest,
) -> MessageResponse:
    email = None
    with db.begin():
        user = user_repo.get_user_by_email_for_update(db, request.email)

        if user is not None:
            email = user.email
            raw_token = secrets.token_urlsafe(32)
            token_hash = hash_password(raw_token)
            expires_at = datetime.now(timezone.utc) + timedelta(
                minutes=RESET_TOKEN_EXPIRE_MINUTES
            )

            password_reset_repo.expire_previous_tokens(db, user.user_id)
            password_reset_repo.create_password_reset_token(
                db=db,
                user_id=user.user_id,
                token_hash=token_hash,
                expires_at=expires_at,
            )

    # send only after the replacement token has been committed.
    if email is not None:
        try:
            send_password_reset_email(email, raw_token, RESET_TOKEN_EXPIRE_MINUTES)
        except ResendError:
            logger.error("Password reset email delivery failed")

    return MessageResponse(
        message="If the email exists, a password reset link has been sent",
    )


def reset_password(
    db: Session,
    request: ResetPasswordRequest,
) -> MessageResponse:
    # every changes in database will be auto flushed to db if we use this
    with db.begin():
        available_tokens = password_reset_repo.get_available_reset_tokens(db)
        matched_token = None

        for reset_token in available_tokens:
            if verify_password(request.token, reset_token.token_hash):
                # the row is locked here
                matched_token = password_reset_repo.get_reset_token_for_update(
                    db, reset_token.reset_token_id
                )
                break

        # another request may have consumed the token while we waited
        if (
            matched_token is None
            or matched_token.used_at is not None
            or matched_token.expires_at <= datetime.now(timezone.utc)
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        user = user_repo.get_user_by_id(db, matched_token.user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        user_repo.update_user_password(
            db=db,
            user=user,
            password_hash=hash_password(request.new_password),
        )
        password_reset_repo.mark_token_used(db, matched_token)

    return MessageResponse(message="Password has been reset successfully")
