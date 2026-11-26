"""Yagona XP va kunlik faollik hisobi (CLAUDE.md, 5-bosqich).

* Har XP manbasi bugungi hisobga (daily_stats, Toshkent sanasi) manba nomi bilan yoziladi:
  test, imtihon, kartochka, oldin (o'yin), taklif.
* Haftalik reyting: test va imtihon XP'si javoblardan hisoblanadi, qolganlari — XpBonus yozuvlaridan.
* Faollik (test javobi, karta, o'yin javobi) ketma-ket kunlarni saqlaydi va kunlik maqsadga kiradi.
* Limitlar Toshkent vaqti bilan 00:00 da yangilanadi (har kun — yangi daily_stats qatori).
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import User, XpBonus
from app.services.facts import get_daily_stat
from app.services.streak import touch_streak

CARD_XP = 2
CARD_XP_CAP = 60          # kartochkalardan kuniga ko'pi bilan
# Javoblardan hisoblanadigan manbalar (reytingga alohida XpBonus yozilmaydi)
ANSWER_SOURCES = {"test", "imtihon"}
SOURCE_LABELS = {"test": "Testlar", "imtihon": "Imtihon", "kartochka": "Kartochkalar",
                 "oldin": "Qaysi biri oldin?", "taklif": "Do‘st taklifi", "taklif_bonus": "Taklif sovg‘asi"}


async def source_xp_today(session: AsyncSession, user_id: int, source: str) -> int:
    stat = await get_daily_stat(session, user_id)
    return int((stat.game_xp or {}).get(source, 0)) if stat else 0


async def award(session: AsyncSession, user_id: int, amount: int, source: str, cap: int | None = None) -> int:
    """XP beradi (cap — shu manbadan kunlik chegara). Haqiqatda berilgan XP'ni qaytaradi."""
    stat = await get_daily_stat(session, user_id, create=True)
    by_source = dict(stat.game_xp or {})
    if cap is not None:
        amount = max(0, min(amount, cap - int(by_source.get(source, 0))))
    if amount <= 0:
        return 0
    by_source[source] = int(by_source.get(source, 0)) + amount
    stat.game_xp = by_source
    stat.xp += amount
    if source not in ANSWER_SOURCES:
        session.add(XpBonus(user_id=user_id, amount=amount, reason=source))
    await session.flush()
    return amount


async def count_actions(session: AsyncSession, user: User, n: int = 1) -> bool:
    """Faollikni hisoblaydi va ketma-ket kunlarni yangilaydi. Streak oshgan bo'lsa True."""
    if n <= 0:
        return False
    stat = await get_daily_stat(session, user.id, create=True)
    stat.actions += n
    return touch_streak(user)


async def actions_today(session: AsyncSession, user_id: int) -> int:
    stat = await get_daily_stat(session, user_id)
    return stat.actions if stat else 0


def goal() -> int:
    return settings.daily_question_count
