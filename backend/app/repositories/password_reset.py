from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.user import PasswordResetToken


def create_password_reset_token(
    db: Session,
    user_id: int,
    token_hash: str,
    expires_at: datetime,
) -> PasswordResetToken:
    reset_token = PasswordResetToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        used_at=None,
    )

    db.add(reset_token)
    db.commit()
    db.refresh(reset_token)

    return reset_token


def get_available_reset_tokens(db: Session) -> list[PasswordResetToken]:
    now = datetime.now(timezone.utc)

    return list(
        db.scalars(
            select(PasswordResetToken).where(
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at > now,
            )
        )
    )


def mark_token_used(
    db: Session,
    reset_token: PasswordResetToken,
) -> PasswordResetToken:
    reset_token.used_at = datetime.now(timezone.utc)

    db.add(reset_token)
    db.commit()
    db.refresh(reset_token)

    return reset_token