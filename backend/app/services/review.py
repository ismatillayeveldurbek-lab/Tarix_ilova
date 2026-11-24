"""Xatolar ustida ishlash — Leitner tizimi (oraliqli takrorlash).

Noto'g'ri javob berilgan savol 0-qutiga tushadi va ertaga qayta beriladi.
Har to'g'ri javobda keyingi qutiga o'tadi, oraliq esa uzayadi.
Oxirgi qutidan ham to'g'ri o'tsa — "o'zlashtirildi" deb belgilanadi.
"""
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import utcnow
from app.models import ReviewItem

INTERVALS_DAYS = [1, 2, 4, 7, 15, 30]  # qutilar 0..5


async def update_review(
    session: AsyncSession, user_id: int, question_id: int, is_correct: bool,
    now: datetime | None = None,
) -> None:
    now = now or utcnow()
    item = await session.scalar(
        select(ReviewItem).where(
            ReviewItem.user_id == user_id, ReviewItem.question_id == question_id
        )
    )
    if not is_correct:
        if item is None:
            item = ReviewItem(user_id=user_id, question_id=question_id)
            session.add(item)
        item.box = 0
        item.mastered = False
        item.next_review_at = now + timedelta(days=INTERVALS_DAYS[0])
        item.last_reviewed_at = now
        return

    # To'g'ri javob: faqat takrorlash vaqti kelgan savol keyingi qutiga o'tadi
    if item is None or item.mastered or item.next_review_at > now:
        return
    item.last_reviewed_at = now
    if item.box + 1 >= len(INTERVALS_DAYS):
        item.mastered = True
    else:
        item.box += 1
        item.next_review_at = now + timedelta(days=INTERVALS_DAYS[item.box])


async def due_question_ids(session: AsyncSession, user_id: int, limit: int) -> list[int]:
    rows = await session.scalars(
        select(ReviewItem.question_id)
        .where(
            ReviewItem.user_id == user_id,
            ReviewItem.mastered.is_(False),
            ReviewItem.next_review_at <= utcnow(),
        )
        .order_by(ReviewItem.next_review_at)
        .limit(limit)
    )
    return list(rows)


async def due_count(session: AsyncSession, user_id: int) -> int:
    return await session.scalar(
        select(func.count()).select_from(ReviewItem).where(
            ReviewItem.user_id == user_id,
            ReviewItem.mastered.is_(False),
            ReviewItem.next_review_at <= utcnow(),
        )
    ) or 0
