"""API v1 — faktlar bazasiga qurilgan yangi qism (CLAUDE.md, MVP bosqichlari).

Eski /api/... marshrutlari Mini App’ning hozirgi sahifalari uchun ishlashda davom etadi.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.deps import CurrentUser, Session
from app.models import Fact, GameSession, UserFactState
from app.services import cards, game_oldin, srs
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


# ---------- O'yin: "Qaysi biri oldin?" ----------

async def _own_game(session, sid: int, user) -> GameSession:
    s = await session.get(GameSession, sid)
    if s is None or s.user_id != user.id or s.game != game_oldin.GAME:
        raise HTTPException(404, "O‘yin topilmadi")
    return s


@router.get("/games/oldin")
async def oldin_info(user: CurrentUser, session: Session) -> dict:
    stat = await get_daily_stat(session, user.id)
    current = await game_oldin.open_session(session, user)
    return {
        "xp_today": int((stat.game_xp or {}).get(game_oldin.GAME, 0)) if stat else 0,
        "xp_cap": game_oldin.DAILY_XP_CAP,
        "rounds_today": await game_oldin.rounds_today(session, user),
        "can_resume": bool(current and game_oldin.left_ms(current) > 0
                           and current.state["idx"] < len(current.state["pairs"])),
        "pairs": game_oldin.PAIRS, "seconds": game_oldin.BUDGET_MS // 1000,
    }


@router.post("/games/oldin/start")
async def oldin_start(user: CurrentUser, session: Session) -> dict:
    try:
        s = await game_oldin.start(session, user)
    except game_oldin.GameError as e:
        raise HTTPException(400, str(e)) from None
    pair = await game_oldin.next_pair(session, s)
    await session.commit()
    return {"session_id": s.id, "round": s.round_no, "pair": pair, "left_ms": game_oldin.left_ms(s),
            "score": s.state["score"], "combo": s.state["combo"]}


class PickIn(BaseModel):
    pick: str = Field(pattern="^[ab]$")


@router.post("/games/{sid}/answer")
async def oldin_answer(sid: int, body: PickIn, user: CurrentUser, session: Session) -> dict:
    s = await _own_game(session, sid, user)
    try:
        res = await game_oldin.answer(session, s, body.pick)
    except game_oldin.GameError as e:
        raise HTTPException(409, str(e)) from None
    await session.commit()
    return res


@router.post("/games/{sid}/next")
async def oldin_next(sid: int, user: CurrentUser, session: Session) -> dict:
    s = await _own_game(session, sid, user)
    pair = await game_oldin.next_pair(session, s)
    await session.commit()
    return {"pair": pair, "left_ms": game_oldin.left_ms(s), "finished": pair is None}


@router.post("/games/{sid}/finish")
async def oldin_finish(sid: int, user: CurrentUser, session: Session) -> dict:
    s = await _own_game(session, sid, user)
    res = await game_oldin.finish(session, user, s)
    await session.commit()
    return res
