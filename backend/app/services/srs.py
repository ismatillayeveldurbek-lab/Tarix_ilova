"""Kunlik takrorlash (oraliqli takrorlash, SRS) — CLAUDE.md, 3-bosqich.

Holatlar: yangi → o'rganilmoqda → o'zlashtirildi; xato bo'lsa — takrorlash kerak.
  * "Bilmadim": 10 daqiqadan keyin qaytadi, oraliq boshidan boshlanadi.
  * "Bildim": oraliq oshib boradi — 1, 4, 10, 25, 60 kun.
    25 kunlik oraliqqa chiqqan karta "o'zlashtirildi" hisoblanadi (lekin vaqti kelganda
    yana tekshiriladi, unutilmasligi uchun).
Hamma hisob serverda; klient faqat ko'rsatadi.
"""
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import utcnow
from app.models import STATE_DUE, STATE_LEARNING, STATE_MASTERED, STATE_NEW, Fact, User, UserFactState
from app.services.cards import card_ok
from app.services.facts import VISIBLE, get_daily_stat
from app.services.xp import CARD_XP, CARD_XP_CAP, award, count_actions

INTERVALS_DAYS = [1, 4, 10, 25, 60]
RELEARN = timedelta(minutes=10)
MASTERED_STEP = 4          # 25 kunlik oraliqqa chiqqanda
NEW_PER_DAY = 20           # kuniga yangi kartalar


def _filters(query, tur: str = "", davr: str = "", book_id: str = ""):
    if tur:
        query = query.where(Fact.tur == tur)
    if davr:
        query = query.where(Fact.davr == davr)
    if book_id:
        query = query.where(Fact.book_id == book_id)
    return query


async def new_cards_left(session: AsyncSession, user: User) -> int:
    stat = await get_daily_stat(session, user.id)
    return max(0, NEW_PER_DAY - (stat.new_cards if stat else 0))


async def queue(session: AsyncSession, user: User, limit: int = 20, tur: str = "", davr: str = "",
                book_id: str = "", now: datetime | None = None) -> list[Fact]:
    """Navbat: avval vaqti kelgan kartalar, keyin yangilari (darslik tartibida, kunlik limit bilan)."""
    now = now or utcnow()
    due = list(await session.scalars(_filters(
        select(Fact).join(UserFactState, UserFactState.fact_id == Fact.id)
        .where(UserFactState.user_id == user.id, UserFactState.next_review_at <= now, VISIBLE)
        .order_by(UserFactState.next_review_at), tur, davr, book_id).limit(limit * 2)))
    cards = [f for f in due if card_ok(f)][:limit]
    room = min(limit - len(cards), await new_cards_left(session, user))
    if room > 0:
        seen = select(UserFactState.fact_id).where(UserFactState.user_id == user.id)
        fresh = await session.scalars(_filters(
            select(Fact).where(VISIBLE, Fact.id.not_in(seen))
            .order_by(Fact.sinf, Fact.book_id, Fact.id), tur, davr, book_id).limit(room * 2))
        cards += [f for f in fresh if card_ok(f)][:room]
    return cards


def schedule(state: UserFactState, knew: bool, now: datetime) -> None:
    """Javobga qarab keyingi ko'rsatish vaqtini belgilaydi."""
    state.last_seen_at = now
    if not knew:
        state.wrong_count += 1
        state.step = 0
        state.holat = STATE_DUE
        state.next_review_at = now + RELEARN
        return
    state.correct_count += 1
    interval = INTERVALS_DAYS[min(state.step, len(INTERVALS_DAYS) - 1)]
    state.step = min(state.step + 1, len(INTERVALS_DAYS))
    state.next_review_at = now + timedelta(days=interval)
    state.holat = STATE_MASTERED if state.step >= MASTERED_STEP else STATE_LEARNING


async def grade(session: AsyncSession, user: User, fact: Fact, knew: bool, now: datetime | None = None) -> UserFactState:
    now = now or utcnow()
    state = await session.scalar(
        select(UserFactState).where(UserFactState.user_id == user.id, UserFactState.fact_id == fact.id))
    stat = await get_daily_stat(session, user.id, create=True)
    if state is None:
        state = UserFactState(user_id=user.id, fact_id=fact.id, holat=STATE_NEW, step=0, correct_count=0, wrong_count=0)
        session.add(state)
        stat.new_cards += 1
    schedule(state, knew, now)
    stat.cards_reviewed += 1
    await count_actions(session, user)
    await award(session, user.id, CARD_XP, "kartochka", cap=CARD_XP_CAP)
    await session.flush()
    return state


async def summary(session: AsyncSession, user: User, now: datetime | None = None) -> dict:
    """Bo'limlar bo'yicha: jami, o'zlashtirilgan, o'rganilmoqda, takrorga (hozir)."""
    now = now or utcnow()
    totals = dict((await session.execute(select(Fact.tur, func.count()).where(VISIBLE).group_by(Fact.tur))).all())
    rows = (await session.execute(
        select(Fact.tur, UserFactState.holat, (UserFactState.next_review_at <= now), func.count())
        .join(UserFactState, UserFactState.fact_id == Fact.id)
        .where(UserFactState.user_id == user.id, VISIBLE)
        .group_by(Fact.tur, UserFactState.holat, (UserFactState.next_review_at <= now))
    )).all()
    out = {t: {"total": n, "mastered": 0, "learning": 0, "due": 0} for t, n in totals.items()}
    for tur, holat, is_due, n in rows:
        o = out.setdefault(tur, {"total": 0, "mastered": 0, "learning": 0, "due": 0})
        if holat == STATE_MASTERED:
            o["mastered"] += n
        else:
            o["learning"] += n
        if is_due:
            o["due"] += n
    due_total = sum(o["due"] for o in out.values())
    return {"sections": out, "due": due_total, "new_left": await new_cards_left(session, user),
            "new_per_day": NEW_PER_DAY}
