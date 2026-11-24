"""Faqat botni ishga tushirish (Mini App'siz).

    python -m app.bot.main

To'liq ilova (bot + Mini App + admin panel) uchun:  python -m app.main
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, MenuButtonWebApp

from app.bot.handlers import admin, menu, quiz, report, settings as settings_handlers, start
from app.bot.keyboards import webapp
from app.bot.middlewares import DbUserMiddleware
from app.bot.scheduler import create_scheduler
from app.config import settings

log = logging.getLogger(__name__)


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


def create_bot() -> Bot:
    if not settings.bot_token or ":" not in settings.bot_token:
        raise SystemExit(
            "BOT_TOKEN topilmadi. backend/.env faylini yarating (.env.example'dan nusxa oling) "
            "va @BotFather bergan tokenni yozing."
        )
    return Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


async def prepare_bot(bot: Bot) -> None:
    """Buyruqlar ro'yxati va (bo'lsa) Mini App menyu tugmasini o'rnatadi."""
    await bot.set_my_commands([
        BotCommand(command="start", description="Boshlash / Бошлаш"),
        BotCommand(command="bugun", description="Tarixda bugun / Тарихда бугун"),
        BotCommand(command="alifbo", description="Lotin / Кирилл"),
    ])
    if settings.webapp_url:
        await bot.set_chat_menu_button(menu_button=MenuButtonWebApp(text="📱 Ilova", web_app=webapp()))
    me = await bot.get_me()
    log.info("Bot ishga tushdi: @%s", me.username)


def setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("apscheduler").setLevel(logging.WARNING)


async def main() -> None:
    setup_logging()
    bot = create_bot()
    dp = create_dispatcher()
    await prepare_bot(bot)
    scheduler = create_scheduler(bot)
    scheduler.start()
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    asyncio.run(main())
