"""Haftalik reyting. Ball (XP): to'g'ri javob — 10, noto'g'ri — 1 (harakat uchun)."""
from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import local_today
from app.models import Answer, User

XP_CORRECT = 10
XP_WRONG = 1
XP_EXPR = func.sum(case((Answer.is_correct.is_(True), XP_CORRECT), else_=XP_WRONG))


def week_start_utc() -> datetime:
    """Joriy hafta boshi (dushanba 00:00, Toshkent vaqti) — UTC'da."""
    today = local_today()
    monday = today - timedelta(days=today.weekday())
    return datetime.combine(monday, time.min, settings.tz).astimezone(UTC).replace(tzinfo=None)


@dataclass
class RatingRow:
    rank: int
    user_id: int
    name: str
    xp: int


def xp_for(is_correct: bool) -> int:
    return XP_CORRECT if is_correct else XP_WRONG


async def weekly_leaderboard(session: AsyncSession, limit: int = 50) -> list[RatingRow]:
    xp = XP_EXPR.label("xp")
    rows = await session.execute(
        select(User.id, User.full_name, xp)
        .join(Answer, Answer.user_id == User.id)
        .where(Answer.answered_at >= week_start_utc())
        .group_by(User.id, User.full_name)
        .order_by(xp.desc(), User.id)
        .limit(limit)
    )
    return [RatingRow(i, uid, name or "Foydalanuvchi", int(x)) for i, (uid, name, x) in enumerate(rows, 1)]


async def user_week_xp(session: AsyncSession, user_id: int) -> int:
    return int(await session.scalar(
        select(func.coalesce(XP_EXPR, 0)).where(
            Answer.user_id == user_id, Answer.answered_at >= week_start_utc()
        )
    ) or 0)


async def user_rank(session: AsyncSession, user_id: int) -> int | None:
    """Foydalanuvchining shu haftadagi o'rni (javob bermagan bo'lsa None)."""
    my_xp = await user_week_xp(session, user_id)
    if my_xp == 0:
        return None
    sub = (
        select(Answer.user_id, XP_EXPR.label("xp"))
        .where(Answer.answered_at >= week_start_utc())
        .group_by(Answer.user_id).subquery()
    )
    higher = await session.scalar(
        select(func.count()).select_from(sub).where(
            (sub.c.xp > my_xp) | ((sub.c.xp == my_xp) & (sub.c.user_id < user_id))
        )
    )
    return (higher or 0) + 1
