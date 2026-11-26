"""Profil, reyting, imtihon (Mini App’ga yo‘naltirish), "Tarixda bugun"."""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards import list_kb, webapp_button_kb
from app.bot.texts import t
from app.bot.utils import esc, leave_input_state
from app.db import local_today
from app.models import User
from app.services.exam import expected_questions, get_active_config
from app.services.history import events_for, format_post
from app.services.progress import overall_percent, recommendation, topic_progress, weak_topics
from app.services.rating import user_rank, user_week_xp, weekly_leaderboard
from app.services.review import due_count
from app.services.stats import answer_totals
from app.services.streak import effective_streak

router = Router(name="menu")
MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}


@router.message(F.text == t("btn_profile"))
async def profile(message: Message, user: User, session: AsyncSession, state: FSMContext) -> None:
    await leave_input_state(state)
    total, correct = await answer_totals(session, user.id)
    items = await topic_progress(session, user.id)
    text = t(
        "profile", total=total, correct=correct,
        percent=round(100 * correct / total) if total else 0,
        streak=effective_streak(user), best=user.streak_best,
        due=await due_count(session, user.id), mastery=overall_percent(items),
    )
    weak = weak_topics(items)
    kb = None
    if weak:
        text += t("weak_title")
        kb = list_kb([(f"▶️ {w.name} — {w.accuracy}%", f"tp:{w.id}") for w in weak])
    else:
        rec = recommendation(items)
        if rec:
            text += t("new_topic_hint", name=esc(rec["name"]))
            kb = list_kb([(f"▶️ {rec['name']}", f"tp:{rec['id']}")])
    await message.answer(text, reply_markup=kb)


@router.message(F.text == t("btn_rating"))
async def rating(message: Message, user: User, session: AsyncSession, state: FSMContext) -> None:
    await leave_input_state(state)
    rows = await weekly_leaderboard(session, limit=10)
    if not rows:
        await message.answer(t("rating_empty"))
        return
    lines = [t("rating_title"), ""]
    for r in rows:
        mark = " 👈" if r.user_id == user.id else ""
        lines.append(f"{MEDALS.get(r.rank, f'{r.rank}.')} {esc(r.name)} — <b>{r.xp}</b> XP{mark}")
    place = await user_rank(session, user.id)
    lines.append("")
    lines.append(
        t("rating_you", place=place, xp=await user_week_xp(session, user.id)) if place
        else t("rating_you_none")
    )
    await message.answer("\n".join(lines))


@router.message(F.text == t("btn_exam"))
async def exam(message: Message, user: User, session: AsyncSession, state: FSMContext) -> None:
    await leave_input_state(state)
    config = await get_active_config(session)
    if config is None:
        await message.answer(t("exam_not_configured"))
        return
    kb = webapp_button_kb(t("btn_open_exam"), "exam")
    text = t("exam_open", name=esc(config.name), count=await expected_questions(session, config),
             minutes=config.duration_minutes)
    await message.answer(text if kb else text + "\n\n" + t("webapp_missing"), reply_markup=kb)


@router.message(Command("bugun"))
async def history_today(message: Message, user: User, session: AsyncSession) -> None:
    today = local_today()
    events = await events_for(session, today)
    if not events:
        await message.answer(t("history_none"))
        return
    await message.answer(format_post(events, today))
