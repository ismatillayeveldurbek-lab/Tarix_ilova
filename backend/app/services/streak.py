"""Kunlik streak: ketma-ket necha kun faol bo‘lganini hisoblaydi."""
from datetime import date, timedelta

from app.db import local_today
from app.models import User


def touch_streak(user: User, today: date | None = None) -> bool:
    """Bugungi faollikni belgilaydi. Streak oshgan bo‘lsa True qaytaradi."""
    today = today or local_today()
    if user.last_active_date == today:
        return False
    if user.last_active_date == today - timedelta(days=1):
        user.streak_current += 1
    else:
        user.streak_current = 1
    user.streak_best = max(user.streak_best, user.streak_current)
    user.last_active_date = today
    return True


def effective_streak(user: User, today: date | None = None) -> int:
    """Ko‘rsatish uchun: kecha yoki bugun faol bo‘lmagan bo‘lsa, ketma-ketlik uzilgan (0)."""
    today = today or local_today()
    if user.last_active_date and user.last_active_date >= today - timedelta(days=1):
        return user.streak_current
    return 0
