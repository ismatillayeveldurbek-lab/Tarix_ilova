"""Foydalanuvchi statistikasi: bosh sahifa va profil uchun."""
from sqlalchemy import Integer, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Answer, User
from app.services.progress import group_by_period, topic_progress


async def answer_totals(session: AsyncSession, user_id: int) -> tuple[int, int]:
    total, correct = (await session.execute(
        select(func.count(), func.coalesce(func.sum(cast(Answer.is_correct, Integer)), 0))
        .where(Answer.user_id == user_id)
    )).one()
    return int(total), int(correct)


async def learning_path(session: AsyncSession, user: User) -> list[dict]:
    """Davrlar -> mavzular: har mavzuda nechta savol va nechtasi o'zlashtirilgan."""
    groups = group_by_period(await topic_progress(session, user.id))
    return [
        {"id": g["id"], "name": g["name"], "topics": [
            {"id": t["id"], "name": t["name"], "total": t["total"], "solved": t["mastered"], "percent": t["percent"]}
            for t in g["topics"]
        ]}
        for g in groups
    ]
