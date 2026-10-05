from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.user import User


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.scalar(
        select(User).where(User.user_id == user_id)
    )


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.scalar(
        select(User).where(User.username == username)
    )


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(
        select(User).where(User.email == email)
    )

def get_user_by_email_for_update(db: Session, email: str) -> User | None:
    return db.scalar(
        select(User)
        .where(User.email == email)
        .with_for_update()
        .execution_options(populate_existing=True)
    )


def create_user(
    db: Session,
    username: str,
    email: str,
    password_hash: str,
) -> User:
    user = User(
        username=username,
        email=email,
        password_hash=password_hash,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def update_user_password(
    db: Session,
    user: User,
    password_hash: str,
) -> User:
    user.password_hash = password_hash

    db.add(user)

    return user