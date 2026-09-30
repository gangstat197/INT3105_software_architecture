from .base import Base
from typing import Optional, List
from sqlalchemy import Text, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Deck(Base):
    __tablename__= "deck"

    deck_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)

    cards: Mapped[List["Card"]] = relationship(
        back_populates= "deck", cascade="all, delete-orphan"
    )

    quizzes: Mapped[List["Quiz"]] = relationship(
        back_populates= "deck", cascade="all, delete-orphan"
    )
