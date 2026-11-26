"""Sinov imtihoni. Format JSON’da saqlanadi — rasmiy spetsifikatsiya chiqqanda
kodni emas, faqat sozlamani o‘zgartirasiz."""
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, utcnow


class ExamConfig(Base):
    __tablename__ = "exam_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    # Masalan: [{"period": "O‘rta asrlar", "difficulty": 2, "count": 10, "points": 1.5}]
    rules: Mapped[list] = mapped_column(JSON, default=list)
    # Masalan: {"max_score": 100}
    scoring: Mapped[dict] = mapped_column(JSON, default=dict)
    # Masalan: [{"min": 70, "grade": "A+"}, {"min": 65, "grade": "A"}, ...]
    grades: Mapped[list] = mapped_column(JSON, default=list)


class ExamSession(Base):
    __tablename__ = "exam_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    config_id: Mapped[int] = mapped_column(ForeignKey("exam_configs.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    deadline_at: Mapped[datetime] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    score: Mapped[float | None] = mapped_column(Float)
    grade: Mapped[str | None] = mapped_column(String(16))


class ExamAnswer(Base):
    __tablename__ = "exam_answers"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("exam_sessions.id"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    position: Mapped[int] = mapped_column(Integer, default=0)
    points: Mapped[float] = mapped_column(Float, default=1.0)
    chosen_option: Mapped[str | None] = mapped_column(String(1))
    is_correct: Mapped[bool | None] = mapped_column(Boolean)
