"""Test mazmuni: davrlar, mavzular, savollar."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, utcnow

OPTIONS = ("a", "b", "c", "d")


class Period(Base):
    __tablename__ = "periods"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    period_id: Mapped[int | None] = mapped_column(ForeignKey("periods.id"))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    period: Mapped[Period | None] = relationship(lazy="joined")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    option_a: Mapped[str] = mapped_column(Text)
    option_b: Mapped[str] = mapped_column(Text)
    option_c: Mapped[str] = mapped_column(Text)
    option_d: Mapped[str] = mapped_column(Text)
    correct_option: Mapped[str] = mapped_column(String(1))  # 'a'..'d'
    explanation: Mapped[str] = mapped_column(Text, default="")

    topic_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id"), index=True)
    period_id: Mapped[int | None] = mapped_column(ForeignKey("periods.id"), index=True)
    difficulty: Mapped[int] = mapped_column(Integer, default=1)  # 1 oson, 2 o‘rta, 3 qiyin
    # Rasm (xarita, portret...): "/api/media/12" (admin yuklagan) yoki https://... havola
    image_url: Mapped[str | None] = mapped_column(String(500))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    # Faktlar bazasidan avtomatik tuzilgan savollar (services/question_gen.py):
    #   gen_key   — "K07J-0012:qachon" (fakt + savol turi); qo‘lda kiritilgan savolda None
    #   asks_time — vaqt so‘raladi: javobdan oldin davr/mavzu ko‘rsatilmaydi (CLAUDE.md)
    #   locked    — admin tahrirlagan: qayta tuzishda ustidan yozilmaydi
    gen_key: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    fact_id: Mapped[str | None] = mapped_column(String(32), index=True)
    asks_time: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    locked: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")

    topic: Mapped[Topic | None] = relationship(lazy="joined")
    period: Mapped[Period | None] = relationship(lazy="joined")

    def option(self, letter: str) -> str:
        return getattr(self, f"option_{letter}")

    @property
    def options(self) -> dict[str, str]:
        return {o: self.option(o) for o in OPTIONS}


class Media(Base):
    """Admin yuklagan rasmlar. Bazada saqlanadi — server qayta joylansa ham yo‘qolmaydi."""

    __tablename__ = "media"

    id: Mapped[int] = mapped_column(primary_key=True)
    mime: Mapped[str] = mapped_column(String(64))
    data: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
