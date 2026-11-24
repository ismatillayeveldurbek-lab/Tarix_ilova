"""Rejalashtirilgan vazifalar (APScheduler):

* har daqiqa — kunlik eslatma vaqti kelgan foydalanuvchilarga eslatma
  (agar bugungi maqsad hali bajarilmagan bo'lsa);
* har kuni HISTORY_POST_TIME da — "Tarixda bugun" posti kanalga va foydalanuvchilarga.
"""
import asyncio
import logging
from datetime import datetime

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import or_, select

from app.bot.broadcast import DELAY, safe_send
from app.bot.keyboards import reminder_kb
from app.bot.texts import t
from app.config import settings
from app.db import SessionLocal, local_today
from app.models import User
from app.services.daily import answers_today
from app.services.history import events_for, format_post

log = logging.getLogger(__name__)


async def send_reminders(bot: Bot, now: datetime | None = None) -> int:
    now = now or datetime.now(settings.tz)
    today = now.date()
    current = now.time().replace(second=0, microsecond=0)
    sent = 0
    async with SessionLocal() as session:
        users = list(await session.scalars(
            select(User).where(
                User.reminder_enabled.is_(True), User.is_blocked.is_(False),
                User.reminder_time == current,
                or_(User.last_reminder_date.is_(None), User.last_reminder_date < today),
            )
        ))
        for user in users:
            user.last_reminder_date = today
            done = await answers_today(session, user.id)
            if done >= settings.daily_question_count:
                continue
            a = user.alphabet
            ok = await safe_send(
                bot, user.telegram_id,
                t("reminder", a, n=settings.daily_question_count - done, streak=user.streak_current),
                reply_markup=reminder_kb(a),
            )
            if ok is False:
                user.is_blocked = True
            sent += bool(ok)
            await asyncio.sleep(DELAY)
        await session.commit()
    if sent:
        log.info("Eslatma yuborildi: %s ta", sent)
    return sent


async def post_history_today(bot: Bot) -> int:
    today = local_today()
    async with SessionLocal() as session:
        events = [e for e in await events_for(session, today) if e.last_posted_year != today.year]
        if not events:
            return 0
        for e in events:  # qayta ishga tushganda ikki marta yuborilmasin
            e.last_posted_year = today.year
        await session.commit()

        if settings.channel_id:
            await safe_send(bot, settings.channel_id, format_post(events, today, "latn"))

        posts = {a: format_post(events, today, a) for a in ("latn", "cyrl")}
        users = list(await session.scalars(select(User).where(User.is_blocked.is_(False))))
        sent = 0
        for user in users:
            ok = await safe_send(bot, user.telegram_id, posts[user.alphabet])
            if ok is False:
                user.is_blocked = True
            sent += bool(ok)
            await asyncio.sleep(DELAY)
        await session.commit()
    log.info("'Tarixda bugun' yuborildi: %s ta foydalanuvchi", sent)
    return sent


def create_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=settings.tz)
    scheduler.add_job(send_reminders, "cron", minute="*", args=[bot], id="reminders",
                      max_instances=1, coalesce=True)
    hour, minute = (int(x) for x in settings.history_post_time.split(":"))
    scheduler.add_job(post_history_today, "cron", hour=hour, minute=minute, args=[bot],
                      id="history_today", max_instances=1, coalesce=True)
    return scheduler


