"""Mavzular bo'yicha o'zlashtirish va zaif mavzular.

* O'zlashtirish (%): mavzudagi savollardan nechtasiga OXIRGI javob to'g'ri bo'lgan.
  Avval to'g'ri, keyin xato javob berilgan savol o'zlashtirilmagan hisoblanadi.
* Aniqlik (%): oxirgi 60 kundagi javoblarning to'g'ri ulushi.
* Zaif mavzu: kamida MIN_ATTEMPTS ta javob va aniqlik WEAK_BELOW % dan past.
"""
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import utcnow
from app.models import Answer, Period, Question, Topic

ACCURACY_WINDOW = timedelta(days=60)
MIN_ATTEMPTS = 3
WEAK_BELOW = 70


@dataclass
class TopicProgress:
    id: int
    name: str
    period_id: int | None
    period_name: str | None
    total: int            # mavzudagi faol savollar
    mastered: int = 0     # oxirgi javobi to'g'ri bo'lgan savollar
    answered: int = 0     # kamida bir marta javob berilgan savollar
    attempts: int = 0     # oxirgi 60 kundagi javoblar soni
    correct: int = 0      # ulardan to'g'ri

    @property
    def percent(self) -> int:
        return round(100 * self.mastered / self.total) if self.total else 0

    @property
    def accuracy(self) -> int | None:
        return round(100 * self.correct / self.attempts) if self.attempts else None

    def as_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "period": self.period_name, "total": self.total,
            "mastered": self.mastered, "answered": self.answered, "attempts": self.attempts,
            "percent": self.percent, "accuracy": self.accuracy,
        }


async def topic_progress(session: AsyncSession, user_id: int) -> list[TopicProgress]:
    """Faol savoli bor har bir mavzu uchun foydalanuvchi natijasi (davr tartibida)."""
    totals = dict((await session.execute(
        select(Question.topic_id, func.count()).where(Question.is_active.is_(True), Question.topic_id.is_not(None))
        .group_by(Question.topic_id)
    )).all())
    rows = (await session.execute(
        select(Topic, Period.name, Period.sort_order).outerjoin(Period, Period.id == Topic.period_id)
        .order_by(Period.sort_order.is_(None), Period.sort_order, Period.id, Topic.sort_order, Topic.id)
    )).all()
    items = {
        t.id: TopicProgress(t.id, t.name, t.period_id, pname, totals[t.id])
        for t, pname, _ in rows if totals.get(t.id)
    }

    answers = await session.execute(
        select(Answer.question_id, Question.topic_id, Answer.is_correct, Answer.answered_at)
        .join(Question, Question.id == Answer.question_id)
        .where(Answer.user_id == user_id, Question.is_active.is_(True), Question.topic_id.is_not(None))
        .order_by(Answer.answered_at, Answer.id)
    )
    since = utcnow() - ACCURACY_WINDOW
    latest: dict[int, tuple[int, bool]] = {}
    for qid, topic_id, ok, at in answers:
        item = items.get(topic_id)
        if item is None:
            continue
        latest[qid] = (topic_id, ok)  # tartib bo'yicha — oxirgisi qoladi
        if at >= since:
            item.attempts += 1
            item.correct += int(ok)
    for topic_id, ok in latest.values():
        items[topic_id].answered += 1
        items[topic_id].mastered += int(ok)
    return list(items.values())


def weak_topics(items: list[TopicProgress], limit: int = 3) -> list[TopicProgress]:
    weak = [i for i in items if i.attempts >= MIN_ATTEMPTS and (i.accuracy or 0) < WEAK_BELOW]
    return sorted(weak, key=lambda i: (i.accuracy or 0, -i.attempts))[:limit]


def recommendation(items: list[TopicProgress]) -> dict | None:
    """Bitta tavsiya: eng zaif mavzu, bo'lmasa hali boshlanmagan birinchi mavzu."""
    weak = weak_topics(items, 1)
    if weak:
        return {"kind": "weak", **weak[0].as_dict()}
    fresh = next((i for i in items if i.answered == 0), None)
    if fresh:
        return {"kind": "new", **fresh.as_dict()}
    return None


def overall_percent(items: list[TopicProgress]) -> int:
    total = sum(i.total for i in items)
    return round(100 * sum(i.mastered for i in items) / total) if total else 0


def group_by_period(items: list[TopicProgress]) -> list[dict]:
    groups: dict[int | None, dict] = {}
    for i in items:
        g = groups.setdefault(i.period_id, {
            "id": i.period_id or 0, "name": i.period_name or "Boshqa mavzular", "topics": [], "_t": 0, "_m": 0,
        })
        g["topics"].append(i.as_dict())
        g["_t"] += i.total
        g["_m"] += i.mastered
    result = []
    for g in groups.values():
        g["percent"] = round(100 * g.pop("_m") / g["_t"]) if g["_t"] else 0
        g["total"] = g.pop("_t")
        result.append(g)
    # "Boshqa mavzular" oxirida
    return sorted(result, key=lambda g: g["id"] == 0)
