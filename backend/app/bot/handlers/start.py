"""/start buyrug'i."""
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.keyboards import main_menu
from app.bot.texts import t
from app.bot.utils import leave_input_state

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await leave_input_state(state)
    await message.answer(t("welcome"), reply_markup=main_menu())
