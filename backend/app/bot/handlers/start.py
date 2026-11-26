"""/start buyrug‘i (referal havolasi bilan ham)."""
from aiogram import Bot, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards import main_menu
from app.bot.referral import notify_joined
from app.bot.texts import t
from app.bot.utils import esc, leave_input_state
from app.config import settings
from app.models import User
from app.services.referrals import parse_ref, register_referral

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(
    message: Message, command: CommandObject, user: User, session: AsyncSession, state: FSMContext, bot: Bot
) -> None:
    await leave_input_state(state)
    await message.answer(t("welcome"), reply_markup=main_menu())

    referral = await register_referral(session, user, parse_ref(command.args))
    if referral:
        inviter = await session.get(User, referral.inviter_id)
        await message.answer(t(
            "ref_welcome", name=esc(inviter.full_name or "do‘stingiz"),
            min=settings.referral_min_answers, xp=settings.referral_xp_invited,
        ))
        await notify_joined(bot, session, referral)
