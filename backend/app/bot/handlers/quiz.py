"""Test oqimi: rejim tanlash -> savollar -> javob + izoh -> yakuniy natija.

Joriy test holati FSM (aiogram xotirasi) ichida saqlanadi:
    quiz = {"ids": [...], "idx": 0, "correct": 0, "answered": False, "source": "practice"}
"""
import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards import after_answer_kb, answer_kb, list_kb, quiz_mode_kb, report_only_kb
from app.bot.texts import both, t
from app.bot.utils import esc, leave_input_state
from app.config import settings
from app.models import Media, Question, User
from app.services.daily import answers_today, daily_question_ids
from app.services.media import media_id
from app.services.quiz import get_question, list_periods, list_topics, pick_question_ids, record_answer
from app.services.rating import xp_for
from app.services.review import due_question_ids
from app.services.translit import tr

router = Router(name="quiz")
log = logging.getLogger(__name__)


# ---------- Ko'rinish ----------

def format_question(q: Question, a: str, n: int, total: int) -> str:
    meta = " · ".join(x for x in (
        q.period.name if q.period else "", q.topic.name if q.topic else ""
    ) if x)
    lines = [t("question_header", a, n=n, total=total) + "  " + "⭐" * q.difficulty]
    if meta:
        lines.append(f"<i>{esc(tr(meta, a))}</i>")
    lines += ["", esc(tr(q.text, a)), ""]
    lines += [f"<b>{letter.upper()})</b> {esc(tr(text, a))}" for letter, text in q.options.items()]
    return "\n".join(lines)


def format_result(q: Question, a: str, chosen: str) -> str:
    if chosen == q.correct_option:
        lines = [t("correct", a)]
    else:
        lines = [
            t("wrong", a, letter=q.correct_option.upper(),
              answer=esc(tr(q.option(q.correct_option), a))),
            t("your_answer", a, letter=chosen.upper()),
        ]
    if q.explanation:
        lines += ["", t("explanation", a, text=esc(tr(q.explanation, a)))]
    return "\n".join(lines)


# ---------- Testni boshlash ----------

async def start_quiz(
    message: Message, state: FSMContext, user: User, session: AsyncSession,
    ids: list[int], source: str = "practice",
) -> None:
    if not ids:
        await message.answer(t("no_questions", user.alphabet))
        return
    quiz = {"ids": ids, "idx": 0, "correct": 0, "xp": 0, "answered": False, "source": source}
    await state.update_data(quiz=quiz)
    await send_current_question(message, state, user, session)


async def send_current_question(
    message: Message, state: FSMContext, user: User, session: AsyncSession
) -> None:
    quiz = (await state.get_data())["quiz"]
    q = await get_question(session, quiz["ids"][quiz["idx"]])
    if q.image_url:
        await send_image(message, session, q.image_url)
    text = format_question(q, user.alphabet, quiz["idx"] + 1, len(quiz["ids"]))
    await message.answer(text, reply_markup=answer_kb(q.id))


async def send_image(message: Message, session: AsyncSession, url: str) -> None:
    """Savol rasmini yuboradi. Rasm ochilmasa ham test davom etadi."""
    try:
        mid = media_id(url)
        if mid:
            media = await session.get(Media, mid)
            if media:
                await message.answer_photo(BufferedInputFile(media.data, filename=f"rasm{mid}.jpg"))
        else:
            await message.answer_photo(url)
    except Exception as e:  # noqa: BLE001 — noto'g'ri havola testni to'xtatmasin
        log.warning("Savol rasmi yuborilmadi (%s): %s", url, e)


@router.message(F.text.in_(both("btn_quiz")))
async def open_quiz_menu(message: Message, user: User, state: FSMContext) -> None:
    await leave_input_state(state)
    await message.answer(t("choose_mode", user.alphabet), reply_markup=quiz_mode_kb(user.alphabet))


@router.message(F.text.in_(both("btn_daily")))
async def open_daily(message: Message, user: User, session: AsyncSession, state: FSMContext) -> None:
    await leave_input_state(state)
    await start_daily(message, state, user, session)


@router.callback_query(F.data == "daily:start")
async def daily_from_reminder(cb: CallbackQuery, user: User, session: AsyncSession, state: FSMContext) -> None:
    await cb.answer()
    await start_daily(cb.message, state, user, session)


async def start_daily(message: Message, state: FSMContext, user: User, session: AsyncSession) -> None:
    ids = await daily_question_ids(session, user.id)
    if ids:
        await message.answer(t("daily_start", user.alphabet, n=len(ids)))
    await start_quiz(message, state, user, session, ids, source="daily")


@router.message(F.text.in_(both("btn_review")))
async def open_review(message: Message, user: User, session: AsyncSession, state: FSMContext) -> None:
    await leave_input_state(state)
    ids = await due_question_ids(session, user.id, settings.quiz_length)
    if not ids:
        await message.answer(t("review_empty", user.alphabet))
        return
    await message.answer(t("review_start", user.alphabet, n=len(ids)))
    await start_quiz(message, state, user, session, ids, source="review")


@router.callback_query(F.data.startswith("qm:"))
async def on_mode(cb: CallbackQuery, user: User, session: AsyncSession, state: FSMContext) -> None:
    a = user.alphabet
    mode = cb.data.split(":")[1]
    if mode == "mixed":
        await cb.message.delete()
        ids = await pick_question_ids(session, settings.quiz_length)
        await start_quiz(cb.message, state, user, session, ids)
    else:
        periods = await list_periods(session)
        prefix = "per" if mode == "period" else "tps"
        key = "choose_period" if mode == "period" else "choose_period_for_topic"
        await cb.message.edit_text(
            t(key, a), reply_markup=list_kb([(p.name, f"{prefix}:{p.id}") for p in periods], a)
        )
    await cb.answer()


@router.callback_query(F.data.startswith("per:"))
async def on_period(cb: CallbackQuery, user: User, session: AsyncSession, state: FSMContext) -> None:
    period_id = int(cb.data.split(":")[1])
    await cb.message.delete()
    ids = await pick_question_ids(session, settings.quiz_length, period_id=period_id)
    await start_quiz(cb.message, state, user, session, ids)
    await cb.answer()


@router.callback_query(F.data.startswith("tps:"))
async def on_period_for_topic(cb: CallbackQuery, user: User, session: AsyncSession) -> None:
    topics = await list_topics(session, int(cb.data.split(":")[1]))
    await cb.message.edit_text(
        t("choose_topic", user.alphabet),
        reply_markup=list_kb([(tp.name, f"tp:{tp.id}") for tp in topics], user.alphabet),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("tp:"))
async def on_topic(cb: CallbackQuery, user: User, session: AsyncSession, state: FSMContext) -> None:
    topic_id = int(cb.data.split(":")[1])
    await cb.message.delete()
    ids = await pick_question_ids(session, settings.quiz_length, topic_id=topic_id)
    await start_quiz(cb.message, state, user, session, ids)
    await cb.answer()


# ---------- Javob berish ----------

@router.callback_query(F.data.startswith("ans:"))
async def on_answer(cb: CallbackQuery, user: User, session: AsyncSession, state: FSMContext) -> None:
    a = user.alphabet
    _, qid_str, chosen = cb.data.split(":")
    qid = int(qid_str)
    quiz = (await state.get_data()).get("quiz")

    # Eski xabardagi tugma bosilgan yoki savolga allaqachon javob berilgan bo'lsa
    if not quiz or quiz["ids"][quiz["idx"]] != qid or quiz["answered"]:
        await cb.answer(t("quiz_expired", a), show_alert=True)
        return

    q = await get_question(session, qid)
    result = await record_answer(session, user, q, chosen, source=quiz["source"])
    quiz["answered"] = True
    quiz["correct"] += int(result.is_correct)
    quiz["xp"] = quiz.get("xp", 0) + xp_for(result.is_correct)
    quiz["had_wrong"] = quiz.get("had_wrong", False) or not result.is_correct
    await state.update_data(quiz=quiz)

    last = quiz["idx"] + 1 >= len(quiz["ids"])
    text = format_question(q, a, quiz["idx"] + 1, len(quiz["ids"])) + "\n\n" + format_result(q, a, chosen)
    await cb.message.edit_text(text, reply_markup=after_answer_kb(q.id, a, last))
    await cb.answer("✅" if result.is_correct else "❌")

    if await answers_today(session, user.id) == settings.daily_question_count:
        await cb.message.answer(t("goal_done", a, n=settings.daily_question_count, streak=user.streak_current))


@router.callback_query(F.data.in_({"nxt", "nxt:c"}))
async def on_next(cb: CallbackQuery, user: User, session: AsyncSession, state: FSMContext) -> None:
    a = user.alphabet
    quiz = (await state.get_data()).get("quiz")
    if not quiz:
        await cb.answer(t("quiz_expired", a), show_alert=True)
        return
    if not quiz["answered"]:  # joriy savolga hali javob berilmagan
        await cb.answer()
        return

    # Oldingi xabardan "Keyingi" tugmasini olib tashlaymiz ("Xato bor" qoladi)
    try:
        if cb.data == "nxt":
            await cb.message.edit_reply_markup(reply_markup=report_only_kb(quiz["ids"][quiz["idx"]], a))
        else:
            await cb.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    quiz["idx"] += 1
    quiz["answered"] = False
    if quiz["idx"] >= len(quiz["ids"]):
        await state.update_data(quiz=None)
        total = len(quiz["ids"])
        text = t("quiz_done", a, correct=quiz["correct"], total=total,
                 percent=round(100 * quiz["correct"] / total), xp=quiz.get("xp", 0),
                 streak=user.streak_current)
        if quiz.get("had_wrong"):
            text += t("quiz_done_review_hint", a)
        await cb.message.answer(text)
    else:
        await state.update_data(quiz=quiz)
        await send_current_question(cb.message, state, user, session)
    await cb.answer()
