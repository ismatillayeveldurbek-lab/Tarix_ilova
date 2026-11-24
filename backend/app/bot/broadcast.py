"""Ko'p foydalanuvchiga xabar yuborish (Telegram limitlariga rioya qilgan holda)."""
import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramNotFound, TelegramRetryAfter
from aiogram.types import InlineKeyboardMarkup

log = logging.getLogger(__name__)
DELAY = 0.05  # sekundiga ~20 ta xabar (Telegram limiti ~30)


async def safe_send(bot: Bot, chat_id: int | str, text: str,
                    reply_markup: InlineKeyboardMarkup | None = None) -> bool | None:
    """True — yuborildi, False — foydalanuvchi botni bloklagan, None — boshqa xato."""
    for _ in range(3):
        try:
            await bot.send_message(chat_id, text, reply_markup=reply_markup)
            return True
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after + 1)
        except (TelegramForbiddenError, TelegramNotFound):
            return False
        except Exception as e:  # noqa: BLE001
            log.warning("Xabar yuborilmadi (%s): %s", chat_id, e)
            return None
    return None


async def broadcast(bot: Bot, recipients: list[tuple[int, str]], text: str, status: dict) -> None:
    """Admin e'loni. recipients: [(telegram_id, alifbo)]. Matn har kimga o'z alifbosida boradi.

    status lug'ati jarayonda yangilanadi — admin panel undan progressni ko'rsatadi.
    """
    import html

    from sqlalchemy import update

    from app.db import SessionLocal
    from app.models import User
    from app.services.translit import tr

    safe = html.escape(text, quote=False)
    texts = {"latn": safe, "cyrl": tr(safe, "cyrl")}
    blocked: list[int] = []
    status.update(total=len(recipients), sent=0, failed=0, running=True)
    try:
        for tid, alphabet in recipients:
            ok = await safe_send(bot, tid, texts.get(alphabet, safe))
            if ok:
                status["sent"] += 1
            else:
                status["failed"] += 1
                if ok is False:
                    blocked.append(tid)
            await asyncio.sleep(DELAY)
    finally:
        status["running"] = False
        if blocked:
            async with SessionLocal() as session:
                await session.execute(update(User).where(User.telegram_id.in_(blocked)).values(is_blocked=True))
                await session.commit()
