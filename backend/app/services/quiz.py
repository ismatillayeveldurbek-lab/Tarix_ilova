"""Test: savollarni tanlash va javobni qayd etish."""
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import utcnow
from app.models import Answer, Period, Question, QuestionReport, Topic, User
from app.services.review import update_review
from app.services.streak import touch_streak


async def pick_question_ids(
    session: AsyncSession,
    count: int,
    topic_id: int | None = None,
    period_id: int | None = None,
) -> list[int]:
    """Tasodifiy tartibda faol savollar ID'larini qaytaradi."""
    q = select(Question.id).where(Question.is_active.is_(True))
    if topic_id:
        q = q.where(Question.topic_id == topic_id)
    if period_id:
        q = q.where(Question.period_id == period_id)
    rows = await session.scalars(q.order_by(func.random()).limit(count))
    return list(rows)


async def get_question(session: AsyncSession, question_id: int) -> Question | None:
    return await session.get(Question, question_id)


@dataclass
class AnswerResult:
    is_correct: bool
    streak_increased: bool


async def record_answer(
    session: AsyncSession, user: User, question: Question, chosen: str, source: str = "practice"
) -> AnswerResult:
    is_correct = chosen == question.correct_option
    session.add(
        Answer(
            user_id=user.id, question_id=question.id, chosen_option=chosen,
            is_correct=is_correct, source=source,
        )
    )
    await update_review(session, user.id, question.id, is_correct)
    streak_up = touch_streak(user)
    await session.flush()
    return AnswerResult(is_correct=is_correct, streak_increased=streak_up)


async def list_periods(session: AsyncSession) -> list[Period]:
    return list(await session.scalars(select(Period).order_by(Period.sort_order, Period.id)))


async def list_topics(session: AsyncSession, period_id: int | None = None) -> list[Topic]:
    q = select(Topic).order_by(Topic.sort_order, Topic.id)
    if period_id:
        q = q.where(Topic.period_id == period_id)
    return list(await session.scalars(q))


REPORTS_PER_DAY = 20  # bitta foydalanuvchi bir kunda yuborishi mumkin bo'lgan xato xabarlari


async def reports_last_day(session: AsyncSession, user_id: int) -> int:
    return await session.scalar(
        select(func.count()).select_from(QuestionReport).where(
            QuestionReport.user_id == user_id, QuestionReport.created_at >= utcnow() - timedelta(days=1))
    ) or 0


async def create_report(
    session: AsyncSession, user: User, question_id: int, comment: str
) -> QuestionReport:
    report = QuestionReport(user_id=user.id, question_id=question_id, comment=comment[:2000])
    session.add(report)
    await session.flush()
    return report
