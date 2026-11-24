"""'⚠️ Xato bor' tugmasi: foydalanuvchi savoldagi xatoni yozib yuboradi."""
import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards import continue_kb, report_admin_kb
from app.bot.texts import t
from app.bot.utils import MENU_TEXTS, esc
from app.config import settings
from app.models import User
from app.services.quiz import REPORTS_PER_DAY, create_report, get_question, reports_last_day

router = Router(name="report")
log = logging.getLogger(__name__)


class ReportStates(StatesGroup):
    waiting_comment = State()


@router.callback_query(F.data.startswith("rep:"))
async def ask_report(cb: CallbackQuery, user: User, state: FSMContext) -> None:
    await state.set_state(ReportStates.waiting_comment)
    await state.update_data(report_qid=int(cb.data.split(":")[1]))
    await cb.message.answer(t("report_ask", user.alphabet))
    await cb.answer()


@router.message(StateFilter(ReportStates.waiting_comment), Command("bekor"))
async def cancel_report(message: Message, user: User, state: FSMContext) -> None:
    await state.set_state(None)
    await message.answer(t("report_cancelled", user.alphabet), reply_markup=_continue(await state.get_data(), user))


@router.message(
    StateFilter(ReportStates.waiting_comment),
    F.text, ~F.text.startswith("/"), ~F.text.in_(MENU_TEXTS),
)
async def save_report(
    message: Message, user: User, session: AsyncSession, state: FSMContext, bot: Bot
) -> None:
    data = await state.get_data()
    qid = data.get("report_qid")
    await state.set_state(None)
    question = await get_question(session, qid) if qid else None
    if question is None:
        return
    if await reports_last_day(session, user.id) >= REPORTS_PER_DAY:
        await message.answer(t("report_limit", user.alphabet), reply_markup=_continue(data, user))
        return
    report = await create_report(session, user, qid, message.text)
    await message.answer(t("report_thanks", user.alphabet), reply_markup=_continue(data, user))

    await notify_admins(bot, report, question, user)


async def notify_admins(bot: Bot, report, question, user: User) -> None:
    """Yangi xato xabari haqida adminlarga darhol yozadi."""
    note = (
        f"⚠️ <b>Yangi xato xabari #{report.id}</b>\n"
        f"Savol #{question.id}: {esc(question.text[:300])}\n"
        f"To'g'ri javob: {question.correct_option.upper()}\n\n"
        f"💬 {esc(report.comment)}\n"
        f"👤 {esc(user.full_name)} (id {user.telegram_id})"
    )
    for admin_id in settings.admin_id_list:
        try:
            await bot.send_message(admin_id, note, reply_markup=report_admin_kb(report.id))
        except Exception as e:  # admin botni hali ochmagan bo'lishi mumkin
            log.warning("Adminga xabar yuborilmadi (%s): %s", admin_id, e)


def _continue(data: dict, user: User):
    """Test davom etayotgan bo'lsa — 'Davom etish' tugmasini ko'rsatamiz."""
    quiz = data.get("quiz")
    return continue_kb(user.alphabet) if quiz and quiz.get("answered") else None
