"""Barcha jadvallar shu yerdan import qilinadi (Alembic ham shu orqali ko‘radi)."""
from app.models.activity import Answer, LessonSession, QuestionReport, ReviewItem
from app.models.content import OPTIONS, Media, Period, Question, Topic
from app.models.exam import ExamAnswer, ExamConfig, ExamSession
from app.models.facts import (
    FACT_TYPES, STATE_DUE, STATE_LEARNING, STATE_MASTERED, STATE_NEW, Book, DailyStat, Fact, UserFactState,
)
from app.models.games import GameSession
from app.models.history import HistoryEvent
from app.models.user import Referral, User, XpBonus

__all__ = [
    "Answer", "LessonSession", "QuestionReport", "ReviewItem", "OPTIONS", "Media", "Period", "Question", "Topic",
    "ExamAnswer", "ExamConfig", "ExamSession", "HistoryEvent", "Referral", "User", "XpBonus",
    "FACT_TYPES", "STATE_DUE", "STATE_LEARNING", "STATE_MASTERED", "STATE_NEW", "Book", "DailyStat", "Fact",
    "UserFactState", "GameSession",
]
