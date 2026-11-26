"""TO‘LIQ ilovani ishga tushirish: Telegram bot + Mini App + admin panel + eslatmalar.

    python -m app.main

Hammasi bitta jarayonda ishlaydi — serverga joylash oson.
"""
import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn

from app.api.app import create_app
from app.bot.main import create_bot, create_dispatcher, prepare_bot, setup_logging
from app.bot.scheduler import create_scheduler
from app.config import settings

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(api):
    bot = create_bot()
    dp = create_dispatcher()
    await prepare_bot(bot)
    scheduler = create_scheduler(bot)
    scheduler.start()
    api.state.bot = bot
    polling = asyncio.create_task(dp.start_polling(bot, handle_signals=False))
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)
        await dp.stop_polling()
        polling.cancel()
        await bot.session.close()


app = create_app(lifespan=lifespan)


if __name__ == "__main__":
    setup_logging()
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
