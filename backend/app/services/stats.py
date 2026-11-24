"""Foydalanuvchi statistikasi: bosh sahifa va profil uchun."""
from sqlalchemy import Integer, cast, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Answer, Period, Question, Topic, User


async def answer_totals(session: AsyncSession, user_id: int) -> tuple[int, int]:
    total, correct = (await session.execute(
        select(func.count(), func.coalesce(func.sum(cast(Answer.is_correct, Integer)), 0))
        .where(Answer.user_id == user_id)
    )).one()
    return int(total), int(correct)


async def learning_path(session: AsyncSession, user: User) -> list[dict]:
    """Davrlar -> mavzular, har bir mavzuda nechta savol bor va nechtasi to'g'ri yechilgan."""
    totals = dict((await session.execute(
        select(Question.topic_id, func.count()).where(Question.is_active.is_(True))
        .group_by(Question.topic_id)
    )).all())
    solved = dict((await session.execute(
        select(Question.topic_id, func.count(distinct(Answer.question_id)))
        .join(Question, Question.id == Answer.question_id)
        .where(Answer.user_id == user.id, Answer.is_correct.is_(True), Question.is_active.is_(True))
        .group_by(Question.topic_id)
    )).all())
    periods = list(await session.scalars(select(Period).order_by(Period.sort_order, Period.id)))
    topics = list(await session.scalars(select(Topic).order_by(Topic.sort_order, Topic.id)))
    result = []
    for p in periods:
        items = [
            {"id": t.id, "name": t.name, "total": totals.get(t.id, 0), "solved": solved.get(t.id, 0)}
            for t in topics if t.period_id == p.id and totals.get(t.id, 0) > 0
        ]
        if items:
            result.append({"id": p.id, "name": p.name, "topics": items})
    # Davri ko'rsatilmagan mavzular ham yo'lda ko'rinsin
    orphans = [
        {"id": t.id, "name": t.name, "total": totals.get(t.id, 0), "solved": solved.get(t.id, 0)}
        for t in topics if t.period_id is None and totals.get(t.id, 0) > 0
    ]
    if orphans:
        result.append({"id": 0, "name": "Boshqa mavzular", "topics": orphans})
    return result
