"""Eslatma vaqtlari xotirada (bepul bazani har daqiqa uyg‘otmaslik uchun).

Eslatma vazifasi har daqiqa ishlaydi. Agar har safar bazaga so‘rov yuborsa, Neon kabi
"jim turganda uxlaydigan" tekin baza hech qachon uxlamaydi va oylik limit tez tugaydi.
Shuning uchun foydalanuvchilar tanlagan vaqtlar to‘plami xotirada saqlanadi: baza faqat
shu daqiqalarda so‘raladi. To‘plam 6 soatda bir yangilanadi va vaqt o‘zgarganda to‘ldiriladi.
"""
from datetime import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import User

_times: set[time] | None = None  # None — hali yuklanmagan: har daqiqa tekshiriladi


def default_time() -> time:
    h, m = (int(x) for x in settings.reminder_time.split(":"))
    return time(h, m)


async def load(session: AsyncSession) -> set[time]:
    global _times
    rows = await session.scalars(select(User.reminder_time).where(User.reminder_enabled.is_(True)).distinct())
    _times = {t.replace(second=0, microsecond=0) for t in rows} | {default_time(), time(19, 0)}
    return _times


def note(t: time) -> None:
    """Foydalanuvchi vaqtni o‘zgartirdi yoki eslatmani yoqdi."""
    if _times is not None:
        _times.add(t.replace(second=0, microsecond=0))


def may_be_due(t: time) -> bool:
    return _times is None or t in _times


def reset() -> None:
    global _times
    _times = None
