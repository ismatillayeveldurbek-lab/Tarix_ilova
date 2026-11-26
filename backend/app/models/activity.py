"""Foydalanuvchi faoliyati: javoblar, takrorlash navbati, xato xabarlari."""
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, utcnow
from app.models.content import Question
from app.models.user import User


class Answer(Base):
    """Har bir berilgan javob. Reyting, streak va statistika shundan hisoblanadi."""

    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), index=True)
    chosen_option: Mapped[str] = mapped_column(String(1))
    is_correct: Mapped[bool] = mapped_column(Boolean)
    source: Mapped[str] = mapped_column(String(16), default="practice")  # practice|daily|review|exam
    answered_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class ReviewItem(Base):
    """Xatolar ustida ishlash: Leitner qutilari (spaced repetition)."""

    __tablename__ = "review_items"
    __table_args__ = (UniqueConstraint("user_id", "question_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    box: Mapped[int] = mapped_column(Integer, default=0)
    next_review_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime)
    mastered: Mapped[bool] = mapped_column(Boolean, default=False)


class QuestionReport(Base):
    """'Savolda xato bor' xabarlari."""

    __tablename__ = "question_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    comment: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(16), default="new", index=True)  # new|fixed|rejected
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user: Mapped[User] = relationship(lazy="joined")
    question: Mapped[Question] = relationship(lazy="joined")


class LessonSession(Base):
    """Mini App darsi: qaysi savollar berilgani va qaysilariga javob berilgani.

    Har bir savolga faqat bir marta javob qabul qilinadi — XP’ni soxta oshirib bo‘lmaydi.
    """

    __tablename__ = "lesson_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    source: Mapped[str] = mapped_column(String(16), default="practice")
    question_ids: Mapped[list] = mapped_column(JSON, default=list)
    answered_ids: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
