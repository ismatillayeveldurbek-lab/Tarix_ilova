"""Botni ishga tushirish nuqtasi.

Ishga tushirish (backend/ papkasida turib):
    python -m app.bot.main
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from app.bot.handlers import admin, menu, quiz, report, settings as settings_handlers, start
from app.bot.middlewares import DbUserMiddleware
from app.config import settings


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    mw = DbUserMiddleware()
    dp.message.outer_middleware(mw)
    dp.callback_query.outer_middleware(mw)
    # Tartib muhim: xato xabari kutilayotganda matn avval report'ga tushadi
    dp.include_routers(
        start.router, report.router, admin.router, quiz.router,
        settings_handlers.router, menu.router,
    )
    return dp


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if not settings.bot_token or ":" not in settings.bot_token:
        raise SystemExit(
            "BOT_TOKEN topilmadi. backend/.env faylini yarating (.env.example'dan nusxa oling) "
            "va @BotFather bergan tokenni yozing."
        )
    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = create_dispatcher()
    await bot.set_my_commands([
        BotCommand(command="start", description="Boshlash / Бошлаш"),
        BotCommand(command="alifbo", description="Lotin / Кирилл"),
    ])
    me = await bot.get_me()
    logging.info("Bot ishga tushdi: @%s", me.username)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
