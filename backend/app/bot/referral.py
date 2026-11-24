"""Referal bildirishnomalari (bot ham, Mini App API ham ishlatadi)."""
import logging

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.broadcast import safe_send
from app.bot.texts import t
from app.bot.utils import esc
from app.config import settings
from app.models import Referral, User

log = logging.getLogger(__name__)


async def bot_username(bot: Bot) -> str:
    if settings.bot_username:
        return settings.bot_username.lstrip("@")
    return (await bot.me()).username or ""


async def notify_joined(bot: Bot, session: AsyncSession, referral: Referral) -> None:
    inviter = await session.get(User, referral.inviter_id)
    invited = await session.get(User, referral.invited_id)
    await safe_send(bot, inviter.telegram_id, t(
        "ref_joined", name=esc(invited.full_name or "Do'stingiz"),
        min=settings.referral_min_answers, xp=settings.referral_xp_inviter,
    ))


async def notify_activated(bot: Bot, session: AsyncSession, referral: Referral) -> None:
    inviter = await session.get(User, referral.inviter_id)
    invited = await session.get(User, referral.invited_id)
    await safe_send(bot, inviter.telegram_id, t(
        "ref_activated", name=esc(invited.full_name or "Do'stingiz"),
        min=settings.referral_min_answers, xp=settings.referral_xp_inviter,
    ))
    await safe_send(bot, invited.telegram_id, t("ref_bonus", xp=settings.referral_xp_invited))
