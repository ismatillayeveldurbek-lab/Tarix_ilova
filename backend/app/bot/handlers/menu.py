"""Profil, reyting, imtihon (Mini App'ga yo'naltirish), "Tarixda bugun"."""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards import webapp_button_kb
from app.bot.texts import both, t
from app.bot.utils import esc, leave_input_state
from app.db import local_today
from app.models import User
from app.services.exam import expected_questions, get_active_config
from app.services.history import events_for, format_post
from app.services.rating import user_rank, user_week_xp, weekly_leaderboard
from app.services.review import due_count
from app.services.stats import answer_totals
from app.services.translit import tr

router = Router(name="menu")
MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}


@router.message(F.text.in_(both("btn_profile")))
async def profile(message: Message, user: User, session: AsyncSession, state: FSMContext) -> None:
    await leave_input_state(state)
    total, correct = await answer_totals(session, user.id)
    await message.answer(t(
        "profile", user.alphabet, total=total, correct=correct,
        percent=round(100 * correct / total) if total else 0,
        streak=user.streak_current, best=user.streak_best,
        due=await due_count(session, user.id),
    ))


@router.message(F.text.in_(both("btn_rating")))
async def rating(message: Message, user: User, session: AsyncSession, state: FSMContext) -> None:
    await leave_input_state(state)
    a = user.alphabet
    rows = await weekly_leaderboard(session, limit=10)
    if not rows:
        await message.answer(t("rating_empty", a))
        return
    lines = [t("rating_title", a), ""]
    for r in rows:
        mark = " 👈" if r.user_id == user.id else ""
        lines.append(f"{MEDALS.get(r.rank, f'{r.rank}.')} {esc(r.name)} — <b>{r.xp}</b> XP{mark}")
    place = await user_rank(session, user.id)
    lines.append("")
    lines.append(
        t("rating_you", a, place=place, xp=await user_week_xp(session, user.id)) if place
        else t("rating_you_none", a)
    )
    await message.answer("\n".join(lines))


@router.message(F.text.in_(both("btn_exam")))
async def exam(message: Message, user: User, session: AsyncSession, state: FSMContext) -> None:
    await leave_input_state(state)
    a = user.alphabet
    config = await get_active_config(session)
    if config is None:
        await message.answer(t("exam_not_configured", a))
        return
    kb = webapp_button_kb(t("btn_open_exam", a), "exam")
    text = t("exam_open", a, name=esc(tr(config.name, a)), count=await expected_questions(session, config),
             minutes=config.duration_minutes)
    await message.answer(text if kb else text + "\n\n" + t("webapp_missing", a), reply_markup=kb)


@router.message(Command("bugun"))
async def history_today(message: Message, user: User, session: AsyncSession) -> None:
    today = local_today()
    events = await events_for(session, today)
    if not events:
        await message.answer(t("history_none", user.alphabet))
        return
    await message.answer(format_post(events, today, user.alphabet))
