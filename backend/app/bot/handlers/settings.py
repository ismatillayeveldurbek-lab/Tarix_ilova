"""Sozlamalar: kunlik eslatma."""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import settings_kb
from app.bot.texts import t
from app.bot.utils import leave_input_state
from app.models import User

router = Router(name="settings")


def settings_text(user: User) -> str:
    reminder = t("on", time=user.reminder_time.strftime("%H:%M")) if user.reminder_enabled else t("off")
    return t("settings", reminder=reminder)


@router.message(F.text == t("btn_settings"))
async def open_settings(message: Message, user: User, state: FSMContext) -> None:
    await leave_input_state(state)
    await message.answer(settings_text(user), reply_markup=settings_kb())


@router.callback_query(F.data == "set:reminder")
async def toggle_reminder(cb: CallbackQuery, user: User) -> None:
    user.reminder_enabled = not user.reminder_enabled
    await cb.message.edit_text(settings_text(user), reply_markup=settings_kb())
    await cb.answer()
