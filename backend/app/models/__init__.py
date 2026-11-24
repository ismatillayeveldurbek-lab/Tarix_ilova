"""Barcha jadvallar shu yerdan import qilinadi (Alembic ham shu orqali ko'radi)."""
from app.models.activity import Answer, QuestionReport, ReviewItem
from app.models.content import OPTIONS, Period, Question, Topic
from app.models.exam import ExamAnswer, ExamConfig, ExamSession
from app.models.history import HistoryEvent
from app.models.user import User

__all__ = [
    "Answer", "QuestionReport", "ReviewItem", "OPTIONS", "Period", "Question", "Topic",
    "ExamAnswer", "ExamConfig", "ExamSession", "HistoryEvent", "User",
]
