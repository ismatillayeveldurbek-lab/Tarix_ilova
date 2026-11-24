"""Sozlamalar: alifbo va kunlik eslatma."""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import main_menu, settings_kb
from app.bot.texts import both, t
from app.bot.utils import leave_input_state
from app.models import User

router = Router(name="settings")


def settings_text(user: User) -> str:
    a = user.alphabet
    reminder = (
        t("on", a, time=user.reminder_time.strftime("%H:%M")) if user.reminder_enabled
        else t("off", a)
    )
    return t("settings", a, alph="Lotin" if a == "latn" else "Кирилл", reminder=reminder)


@router.message(F.text.in_(both("btn_settings")))
async def open_settings(message: Message, user: User, state: FSMContext) -> None:
    await leave_input_state(state)
    await message.answer(settings_text(user), reply_markup=settings_kb(user.alphabet))


@router.callback_query(F.data == "set:alphabet")
async def switch_alphabet(cb: CallbackQuery, user: User) -> None:
    user.alphabet = "cyrl" if user.alphabet == "latn" else "latn"
    user.alphabet_chosen = True
    await cb.message.edit_text(settings_text(user), reply_markup=settings_kb(user.alphabet))
    # Pastki menyu tugmalari ham yangi alifboda bo'lishi uchun yangi xabar yuboramiz
    await cb.message.answer(t("alphabet_saved", user.alphabet), reply_markup=main_menu(user.alphabet))
    await cb.answer()


@router.callback_query(F.data == "set:reminder")
async def toggle_reminder(cb: CallbackQuery, user: User) -> None:
    user.reminder_enabled = not user.reminder_enabled
    await cb.message.edit_text(settings_text(user), reply_markup=settings_kb(user.alphabet))
    await cb.answer()
