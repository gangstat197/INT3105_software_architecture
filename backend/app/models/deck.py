from app.models.base import Base
from app.models.card import Card
from app.models.quiz import Quiz
from typing import Optional
from typing import List
from sqlalchemy import Text
from sqlalchemy import String
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

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
