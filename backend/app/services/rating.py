"""Haftalik reyting. Ball (XP): to‘g‘ri javob — 10, noto‘g‘ri — 1 (harakat uchun)."""
from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta

from sqlalchemy import case, func, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import local_today
from app.models import Answer, User, XpBonus

XP_CORRECT = 10
XP_WRONG = 1


def week_start_utc() -> datetime:
    """Joriy hafta boshi (dushanba 00:00, Toshkent vaqti) — UTC’da."""
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


def _week_xp():
    """Shu haftadagi XP: javoblar + bonuslar (masalan, taklif uchun). Ustunlar: user_id, xp."""
    since = week_start_utc()
    answers = select(
        Answer.user_id.label("user_id"),
        case((Answer.is_correct.is_(True), XP_CORRECT), else_=XP_WRONG).label("xp"),
    ).where(Answer.answered_at >= since)
    bonuses = select(XpBonus.user_id.label("user_id"), XpBonus.amount.label("xp")).where(XpBonus.created_at >= since)
    u = union_all(answers, bonuses).subquery()
    return select(u.c.user_id, func.sum(u.c.xp).label("xp")).group_by(u.c.user_id).subquery()


async def weekly_leaderboard(session: AsyncSession, limit: int = 50) -> list[RatingRow]:
    w = _week_xp()
    rows = await session.execute(
        select(User.id, User.full_name, w.c.xp)
        .join(w, w.c.user_id == User.id)
        .order_by(w.c.xp.desc(), User.id)
        .limit(limit)
    )
    return [RatingRow(i, uid, name or "Foydalanuvchi", int(x)) for i, (uid, name, x) in enumerate(rows, 1)]


async def user_week_xp(session: AsyncSession, user_id: int) -> int:
    w = _week_xp()
    return int(await session.scalar(select(w.c.xp).where(w.c.user_id == user_id)) or 0)


async def user_rank(session: AsyncSession, user_id: int) -> int | None:
    """Foydalanuvchining shu haftadagi o‘rni (XP bo‘lmasa None)."""
    w = _week_xp()
    my_xp = int(await session.scalar(select(w.c.xp).where(w.c.user_id == user_id)) or 0)
    if my_xp == 0:
        return None
    higher = await session.scalar(
        select(func.count()).select_from(w).where(
            (w.c.xp > my_xp) | ((w.c.xp == my_xp) & (w.c.user_id < user_id))
        )
    )
    return (higher or 0) + 1
