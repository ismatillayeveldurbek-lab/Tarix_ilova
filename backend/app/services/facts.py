"""Faktlar bo‘yicha umumiy so‘rovlar."""
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import local_today, utcnow
from app.models import STATE_DUE, STATE_LEARNING, STATE_MASTERED, DailyStat, Fact, User, UserFactState

# Foydalanuvchiga ko‘rsatiladigan faktlar
VISIBLE = and_(Fact.hidden_import.is_(False), Fact.hidden_admin.is_(False))


async def get_daily_stat(session: AsyncSession, user_id: int, create: bool = False) -> DailyStat | None:
    """Bugungi (Toshkent sanasi) hisob. create=True bo‘lsa, yo‘q bo‘lsa yaratadi."""
    today = local_today()
    stat = await session.scalar(select(DailyStat).where(DailyStat.user_id == user_id, DailyStat.day == today))
    if stat is None and create:
        stat = DailyStat(user_id=user_id, day=today, xp=0, cards_reviewed=0, games_played=0, game_xp={})
        session.add(stat)
        await session.flush()
    return stat


async def fact_progress(session: AsyncSession, user: User) -> dict:
    """Faktlar bo‘yicha holatlar: yangi / o‘rganilmoqda / takrorlash kerak / o‘zlashtirildi."""
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


DAVRLAR = ["Qadimgi", "O‘rta asrlar", "Yangi", "Eng yangi"]
TYPE_LABELS = {"sana": "Yillar", "shaxs": "Shaxslar", "atama": "Atamalar", "joy": "Joylar",
               "urush": "Urushlar", "asar": "Asarlar"}


async def fact_path(session: AsyncSession, user: User) -> dict:
    """"Tarix yo‘lingiz": davrlar bo‘yicha o‘zlashtirish va bo‘limlar (turlar) bo‘yicha hajm."""
    totals = dict((await session.execute(
        select(Fact.davr, func.count()).where(VISIBLE).group_by(Fact.davr)
    )).all())
    state_rows = (await session.execute(
        select(Fact.davr, UserFactState.holat, func.count())
        .join(Fact, Fact.id == UserFactState.fact_id)
        .where(UserFactState.user_id == user.id, VISIBLE)
        .group_by(Fact.davr, UserFactState.holat)
    )).all()
    mastered: dict[str, int] = {}
    started: dict[str, int] = {}
    for davr, holat, n in state_rows:
        started[davr] = started.get(davr, 0) + n
        if holat == STATE_MASTERED:
            mastered[davr] = mastered.get(davr, 0) + n
    order = DAVRLAR + sorted(d for d in totals if d not in DAVRLAR)
    davrlar = [
        {"name": d, "total": totals[d], "mastered": mastered.get(d, 0), "started": started.get(d, 0)}
        for d in order if totals.get(d)
    ]
    by_type = dict((await session.execute(
        select(Fact.tur, func.count()).where(VISIBLE).group_by(Fact.tur)
    )).all())
    sections = [{"tur": t, "label": TYPE_LABELS[t], "total": by_type.get(t, 0)} for t in TYPE_LABELS if by_type.get(t)]
    total = sum(x["total"] for x in davrlar)
    return {
        "total": total,
        "mastered": sum(x["mastered"] for x in davrlar),
        "davrlar": davrlar,
        "sections": sections,
    }
