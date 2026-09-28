from app.models.base import Base
from typing import List
from typing import Optional
from sqlalchemy import Text
from sqlalchemy import String
from sqlalchemy import ForeignKey
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

class Word(Base):
    __tablename__= "word"
    __table_args__ = (
        UniqueConstraint("language", "normalized_word", name="unique_constraint_word_language_normalized"), # name is optional but for clarity, can be renamed for shorthand?
    )

    word_id: Mapped[int] = mapped_column(primary_key=True)
    word: Mapped[str] = mapped_column(String(255)) 
    normalized_word: Mapped[str] = mapped_column(String(255))
    language: Mapped[str] = mapped_column(String(10))

    # https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html for relationship pattern
    # word has many meanings -> one to many relationship
    meanings: Mapped[List["WordMeaning"]] = relationship(
        back_populates="word", cascade="all, delete-orphan"
    )

class WordMeaning(Base):
    __tablename__ = "word_meaning"

    word_meaning_id: Mapped[int] = mapped_column(primary_key=True)
    word_id: Mapped[int] = mapped_column(ForeignKey("word.word_id", ondelete="CASCADE"))

    # this doesn't exist in DB, but sqlalchemy recommends related classes to be "synchronized"
    # https://docs.sqlalchemy.org/en/20/orm/relationship_api.html#sqlalchemy.orm.relationship
    word: Mapped["Word"] = relationship(
        back_populates="meanings"
    )

    part_of_speech: Mapped[Optional[str]] = mapped_column(String(255))
    ipa: Mapped[Optional[str]] = mapped_column(String(255))
    audio: Mapped[Optional[str]] = mapped_column(String(512)) # Maybe longer if URL too long?

    # meaning has many definitions
    definitions: Mapped[List["WordDefinition"]] = relationship(
        back_populates="word_meaning", cascade="all, delete-orphan"
    )

class WordDefinition(Base):
    __tablename__ = "word_definition"

    word_definition_id: Mapped[int] = mapped_column(primary_key=True)
    word_meaning_id: Mapped[int] = mapped_column(ForeignKey("word_meaning.word_meaning_id", ondelete="CASCADE"))
    definition: Mapped[str] = mapped_column(Text)
    example: Mapped[Optional[str]] = mapped_column(Text)

    # Same case as above
    word_meaning: Mapped["WordMeaning"] = relationship(back_populates="definitions")

    # each definition has many synonyms and antonyms
    synonyms: Mapped[List["WordSynonym"]] = relationship(
        back_populates="word_definition", cascade="all, delete-orphan"
    )
    antonyms: Mapped[List["WordAntonym"]] = relationship(
        back_populates="word_definition", cascade="all, delete-orphan"
    )

class WordSynonym(Base):
    __tablename__ = "word_synonym"

    synonym_id: Mapped[int] = mapped_column(primary_key=True)
    word_definition_id: Mapped[int] = mapped_column(
        ForeignKey("word_definition.word_definition_id", ondelete="CASCADE")
    )
    word: Mapped[str] = mapped_column(String(255))

    word_definition: Mapped["WordDefinition"] = relationship(back_populates="synonyms")


class WordAntonym(Base):
    __tablename__ = "word_antonym"

    antonym_id: Mapped[int] = mapped_column(primary_key=True)
    word_definition_id: Mapped[int] = mapped_column(
        ForeignKey("word_definition.word_definition_id", ondelete="CASCADE")
    )
    word: Mapped[str] = mapped_column(String(255))

    word_definition: Mapped["WordDefinition"] = relationship(back_populates="antonyms")
