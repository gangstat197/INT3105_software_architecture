from app.models.base import Base
from app.models.deck import Deck
from app.models.word import Word
from typing import Optional
from datetime import datetime
from sqlalchemy import Text
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

class Card(Base):
    __tablename__= "card"

    card_id: Mapped[int] = mapped_column(primary_key=True)
    deck_id: Mapped[int] = mapped_column(ForeignKey("deck.deck_id", ondelete="CASCADE"))
    word_id: Mapped[int] = mapped_column(ForeignKey("word.word_id", ondelete="RESTRICT")) # deleted card don't cascade to word

    deck: Mapped["Deck"] = relationship(back_populates="cards")
    word: Mapped["Word"] = relationship(back_populates="cards")

    notes: Mapped[Optional[str]] = mapped_column(Text)
    progress_level: Mapped[int] = mapped_column(default=1) # initial value set at 1 as new word is set at box 1
    last_reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    next_reviewed_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    review_total_count: Mapped[int] = mapped_column(default=0)
    review_correct_count: Mapped[int] = mapped_column(default=0)
    review_version: Mapped[int] = mapped_column(default=0)


