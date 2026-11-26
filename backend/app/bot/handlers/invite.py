"""'👥 Do‘stlarni taklif qilish' — shaxsiy havola va statistika."""
from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards import invite_kb
from app.bot.referral import bot_username
from app.bot.texts import t
from app.bot.utils import leave_input_state
from app.config import settings
from app.models import User
from app.services.referrals import ensure_ref_code, referral_link, referral_stats

router = Router(name="invite")


@router.message(F.text == t("btn_invite"))
@router.message(Command("taklif"))
async def invite(message: Message, user: User, session: AsyncSession, state: FSMContext, bot: Bot) -> None:
    await leave_input_state(state)
    link = referral_link(await bot_username(bot), await ensure_ref_code(session, user))
    stats = await referral_stats(session, user)
    await message.answer(
        t("invite", min=settings.referral_min_answers, xp_inviter=settings.referral_xp_inviter,
          xp_invited=settings.referral_xp_invited, invited=stats["invited"], active=stats["active"],
          earned=stats["earned_xp"], link=link),
        reply_markup=invite_kb(link), disable_web_page_preview=True,
    )
