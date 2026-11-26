"""API v1 — faktlar bazasiga qurilgan yangi qism (CLAUDE.md, MVP bosqichlari).

Eski /api/... marshrutlari Mini App'ning hozirgi sahifalari uchun ishlashda davom etadi.
"""
from fastapi import APIRouter

from app.api.deps import CurrentUser, Session
from app.services.facts import fact_progress, get_daily_stat
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
