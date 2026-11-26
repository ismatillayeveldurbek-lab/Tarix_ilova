"""API v1 — faktlar bazasiga qurilgan yangi qism (CLAUDE.md, MVP bosqichlari).

Eski /api/... marshrutlari Mini App’ning hozirgi sahifalari uchun ishlashda davom etadi.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import CurrentUser, Session
from app.models import Fact, UserFactState
from app.services import cards, srs
from app.services.cards import card_ok
from app.services.facts import fact_path, fact_progress, get_daily_stat
from app.services.streak import effective_streak

router = APIRouter(prefix="/api/v1")


@router.get("/me")
async def me(user: CurrentUser, session: Session) -> dict:
    today = await get_daily_stat(session, user.id)
    return {
        "user": {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "name": user.full_name,
            "username": user.username,
            "is_admin": user.is_admin,
            "streak": effective_streak(user),
            "streak_best": user.streak_best,
        },
        "today": {
            "xp": today.xp if today else 0,
            "cards_reviewed": today.cards_reviewed if today else 0,
            "games_played": today.games_played if today else 0,
        },
        "facts": await fact_progress(session, user),
    }


@router.get("/path")
async def path(user: CurrentUser, session: Session) -> dict:
    """"Tarix yo‘lingiz": davrlar bo‘yicha o‘zlashtirish va bo‘limlar hajmi."""
    return await fact_path(session, user)


# ---------- Kunlik takrorlash (kartochkalar) ----------

async def _visible_fact(session, fact_id: str) -> Fact:
    fact = await session.get(Fact, fact_id)
    if fact is None or not fact.visible or not card_ok(fact):
        raise HTTPException(404, "Karta topilmadi")
    return fact


@router.get("/cards")
async def cards_queue(user: CurrentUser, session: Session, tur: str = "", davr: str = "", book_id: str = "",
                      limit: int = 20) -> dict:
    """Navbat: faqat kartaning OLD tomoni (javob yuborilmaydi)."""
    facts = await srs.queue(session, user, limit=max(1, min(limit, 50)), tur=tur, davr=davr, book_id=book_id)
    s = await srs.summary(session, user)
    return {"cards": [cards.front(f) for f in facts], "due": s["due"], "new_left": s["new_left"]}


@router.get("/cards/summary")
async def cards_summary(user: CurrentUser, session: Session) -> dict:
    return await srs.summary(session, user)


@router.post("/cards/{fact_id}/reveal")
async def cards_reveal(fact_id: str, user: CurrentUser, session: Session) -> dict:
    """"Javobni ko'rish": kartaning orqa tomoni va darslik manbasi."""
    return cards.back(await _visible_fact(session, fact_id))


class GradeIn(BaseModel):
    knew: bool  # True — "Bildim", False — "Bilmadim"


@router.post("/cards/{fact_id}/grade")
async def cards_grade(fact_id: str, body: GradeIn, user: CurrentUser, session: Session) -> dict:
    fact = await _visible_fact(session, fact_id)
    is_new = not await session.scalar(
        select(UserFactState.id).where(UserFactState.user_id == user.id, UserFactState.fact_id == fact.id))
    if is_new and await srs.new_cards_left(session, user) <= 0:
        raise HTTPException(409, "Bugungi yangi kartalar limiti tugadi. Ertaga davom eting")
    state = await srs.grade(session, user, fact, body.knew)
    await session.commit()
    stat = await get_daily_stat(session, user.id)
    return {
        "holat": state.holat, "step": state.step,
        "next_review_at": state.next_review_at.isoformat() + "Z",
        "today": {"cards_reviewed": stat.cards_reviewed, "new_cards": stat.new_cards},
    }
