"""Faktlar bo'yicha umumiy so'rovlar."""
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import local_today, utcnow
from app.models import STATE_DUE, STATE_LEARNING, STATE_MASTERED, DailyStat, Fact, User, UserFactState

# Foydalanuvchiga ko'rsatiladigan faktlar
VISIBLE = and_(Fact.hidden_import.is_(False), Fact.hidden_admin.is_(False))


async def get_daily_stat(session: AsyncSession, user_id: int, create: bool = False) -> DailyStat | None:
    """Bugungi (Toshkent sanasi) hisob. create=True bo'lsa, yo'q bo'lsa yaratadi."""
    today = local_today()
    stat = await session.scalar(select(DailyStat).where(DailyStat.user_id == user_id, DailyStat.day == today))
    if stat is None and create:
        stat = DailyStat(user_id=user_id, day=today, xp=0, cards_reviewed=0, games_played=0, game_xp={})
        session.add(stat)
        await session.flush()
    return stat


async def fact_progress(session: AsyncSession, user: User) -> dict:
    """Faktlar bo'yicha holatlar: yangi / o'rganilmoqda / takrorlash kerak / o'zlashtirildi."""
    total = await session.scalar(select(func.count()).select_from(Fact).where(VISIBLE)) or 0
    by_state = dict((await session.execute(
        select(UserFactState.holat, func.count())
        .join(Fact, Fact.id == UserFactState.fact_id)
        .where(UserFactState.user_id == user.id, VISIBLE)
        .group_by(UserFactState.holat)
    )).all())
    due_now = await session.scalar(
        select(func.count()).select_from(UserFactState).join(Fact, Fact.id == UserFactState.fact_id)
        .where(UserFactState.user_id == user.id, VISIBLE, UserFactState.holat != STATE_MASTERED,
               UserFactState.next_review_at <= utcnow())
    ) or 0
    started = sum(by_state.values())
    return {
        "total": total,
        "yangi": total - started + by_state.get("yangi", 0),
        "organilmoqda": by_state.get(STATE_LEARNING, 0),
        "takrorlash_kerak": by_state.get(STATE_DUE, 0),
        "ozlashtirildi": by_state.get(STATE_MASTERED, 0),
        "due_now": due_now,
    }
