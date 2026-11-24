"""Kunlik maqsad: kuniga N ta savol. Avval takrorlash vaqti kelganlar, keyin yangilari."""
from datetime import UTC, date, datetime, time

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import local_today
from app.models import Answer, Question
from app.services.review import due_question_ids


def local_midnight_utc(day: date | None = None) -> datetime:
    """Toshkent vaqti bo'yicha kun boshini UTC'da qaytaradi."""
    day = day or local_today()
    return datetime.combine(day, time.min, settings.tz).astimezone(UTC).replace(tzinfo=None)


async def answers_today(session: AsyncSession, user_id: int) -> int:
    return await session.scalar(
        select(func.count()).select_from(Answer).where(
            Answer.user_id == user_id, Answer.answered_at >= local_midnight_utc()
        )
    ) or 0


async def daily_question_ids(session: AsyncSession, user_id: int, count: int | None = None) -> list[int]:
    count = count or settings.daily_question_count
    ids = await due_question_ids(session, user_id, count)
    if len(ids) < count:
        answered = select(Answer.question_id).where(Answer.user_id == user_id)
        fresh = await session.scalars(
            select(Question.id)
            .where(Question.is_active.is_(True), Question.id.not_in(answered), Question.id.not_in(ids or [0]))
            .order_by(func.random()).limit(count - len(ids))
        )
        ids += list(fresh)
    if len(ids) < count:  # hamma savol yechilgan bo'lsa — tasodifiy
        more = await session.scalars(
            select(Question.id)
            .where(Question.is_active.is_(True), Question.id.not_in(ids or [0]))
            .order_by(func.random()).limit(count - len(ids))
        )
        ids += list(more)
    return ids
