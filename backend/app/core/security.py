from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import jwt
from backend.app.core.config import settings


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int, expire_delta: timedelta | None = None, ) -> str:
    if expire_delta is None:
        expire_delta = timedelta(
            minutes=settings.JWT_EXPIRE_MINUTES
        )

    expire = datetime.now(timezone.utc) + expire_delta

    payload = {
        "sub": str(user_id),
        "exp": expire
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.PyJWTError as e:
        print("JWT decode error:", type(e).__name__, e)
        return None