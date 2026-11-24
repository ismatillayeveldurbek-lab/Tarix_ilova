"""/start va alifbo tanlash."""
from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import alphabet_kb, main_menu
from app.bot.texts import t
from app.bot.utils import leave_input_state
from app.models import User

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, user: User, state: FSMContext) -> None:
    await leave_input_state(state)
    if not user.alphabet_chosen:
        await message.answer(t("choose_alphabet"), reply_markup=alphabet_kb())
        return
    await message.answer(t("welcome", user.alphabet), reply_markup=main_menu(user.alphabet))


@router.message(Command("alifbo"))
async def cmd_alphabet(message: Message) -> None:
    await message.answer(t("choose_alphabet"), reply_markup=alphabet_kb())


@router.callback_query(F.data.startswith("alph:"))
async def on_alphabet(cb: CallbackQuery, user: User) -> None:
    user.alphabet = "cyrl" if cb.data == "alph:cyrl" else "latn"
    first_time = not user.alphabet_chosen
    user.alphabet_chosen = True
    a = user.alphabet
    await cb.message.edit_text(t("alphabet_saved", a))
    await cb.message.answer(
        t("welcome", a) if first_time else t("alphabet_saved", a), reply_markup=main_menu(a)
    )
    await cb.answer()
