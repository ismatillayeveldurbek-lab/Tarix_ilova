"""Profil va hali tayyor bo'lmagan bo'limlar."""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import Integer, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.texts import both, t
from app.bot.utils import leave_input_state
from app.models import Answer, User
from app.services.review import due_count

router = Router(name="menu")


@router.message(F.text.in_(both("btn_profile")))
async def profile(message: Message, user: User, session: AsyncSession, state: FSMContext) -> None:
    await leave_input_state(state)
    total, correct = (await session.execute(
        select(func.count(), func.coalesce(func.sum(cast(Answer.is_correct, Integer)), 0))
        .where(Answer.user_id == user.id)
    )).one()
    await message.answer(t(
        "profile", user.alphabet, total=total, correct=correct,
        percent=round(100 * correct / total) if total else 0,
        streak=user.streak_current, best=user.streak_best,
        due=await due_count(session, user.id),
    ))


@router.message(F.text.in_(both("btn_review") | both("btn_exam") | both("btn_rating")))
async def coming_soon(message: Message, user: User, state: FSMContext) -> None:
    await leave_input_state(state)
    await message.answer(t("coming_soon", user.alphabet))
