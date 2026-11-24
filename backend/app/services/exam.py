"""Sinov imtihoni.

Format `exam_configs` jadvalidan olinadi (admin paneldan tahrirlanadi):
  rules  — [{"count": 10, "points": 1.5, "difficulty": 2, "period": "O'rta asrlar", "topic": "..."}]
           (difficulty/period/topic — ixtiyoriy filtrlar)
  scoring — {"max_score": 100}  — natija shu shkalaga keltiriladi
  grades — [{"min_percent": 85, "grade": "A+"}, ...]
"""
from dataclasses import dataclass, field
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import utcnow
from app.models import Answer, ExamAnswer, ExamConfig, ExamSession, Period, Question, Topic, User
from app.services.review import update_review
from app.services.streak import touch_streak

GRACE_SECONDS = 30  # internet sekinligi uchun qo'shimcha vaqt


class ExamError(Exception):
    pass


async def get_active_config(session: AsyncSession) -> ExamConfig | None:
    return await session.scalar(
        select(ExamConfig).where(ExamConfig.is_active.is_(True)).order_by(ExamConfig.id.desc()).limit(1)
    )


def _rule_query(rule: dict):
    q = select(Question.id).where(Question.is_active.is_(True))
    if rule.get("difficulty"):
        q = q.where(Question.difficulty == int(rule["difficulty"]))
    if rule.get("period"):
        q = q.join(Period, Period.id == Question.period_id).where(Period.name == rule["period"])
    if rule.get("topic"):
        q = q.join(Topic, Topic.id == Question.topic_id).where(Topic.name == rule["topic"])
    return q


async def rule_availability(session: AsyncSession, rules: list[dict]) -> list[int]:
    """Har bir qoida uchun bazada nechta mos savol borligi (admin uchun ogohlantirish)."""
    result = []
    for rule in rules:
        result.append(await session.scalar(select(func.count()).select_from(_rule_query(rule).subquery())) or 0)
    return result


def total_questions(config: ExamConfig) -> int:
    return sum(int(r.get("count", 0)) for r in config.rules)


async def expected_questions(session: AsyncSession, config: ExamConfig) -> int:
    """Bazada yetarli savol bo'lmasa, haqiqatda nechta savol berilishini hisoblaydi."""
    avail = await rule_availability(session, config.rules)
    return sum(min(int(r.get("count", 0)), a) for r, a in zip(config.rules, avail))


async def get_open_exam(session: AsyncSession, user: User) -> ExamSession | None:
    exam = await session.scalar(
        select(ExamSession).where(ExamSession.user_id == user.id, ExamSession.finished_at.is_(None))
        .order_by(ExamSession.id.desc()).limit(1)
    )
    if exam and is_expired(exam):
        await finish_exam(session, exam, user)
        return None
    return exam


def is_expired(exam: ExamSession) -> bool:
    return utcnow() > exam.deadline_at + timedelta(seconds=GRACE_SECONDS)


async def start_exam(session: AsyncSession, user: User) -> ExamSession:
    open_exam = await get_open_exam(session, user)
    if open_exam:
        return open_exam
    config = await get_active_config(session)
    if config is None:
        raise ExamError("Imtihon formati sozlanmagan")

    chosen: list[tuple[int, float]] = []
    for rule in config.rules:
        q = _rule_query(rule)
        if chosen:
            q = q.where(Question.id.not_in([c[0] for c in chosen]))
        ids = await session.scalars(q.order_by(func.random()).limit(int(rule.get("count", 0))))
        chosen += [(qid, float(rule.get("points", 1))) for qid in ids]
    if not chosen:
        raise ExamError("Imtihon uchun savollar yetarli emas")

    now = utcnow()
    exam = ExamSession(user_id=user.id, config_id=config.id, started_at=now,
                       deadline_at=now + timedelta(minutes=config.duration_minutes))
    session.add(exam)
    await session.flush()
    for pos, (qid, pts) in enumerate(chosen):
        session.add(ExamAnswer(session_id=exam.id, question_id=qid, position=pos, points=pts))
    await session.flush()
    return exam


async def exam_items(session: AsyncSession, exam: ExamSession) -> list[ExamAnswer]:
    return list(await session.scalars(
        select(ExamAnswer).where(ExamAnswer.session_id == exam.id).order_by(ExamAnswer.position)
    ))


async def save_answer(session: AsyncSession, exam: ExamSession, question_id: int, option: str) -> None:
    if exam.finished_at is not None:
        raise ExamError("Imtihon yakunlangan")
    if is_expired(exam):
        raise ExamError("Vaqt tugagan")
    item = await session.scalar(
        select(ExamAnswer).where(ExamAnswer.session_id == exam.id, ExamAnswer.question_id == question_id)
    )
    if item is None:
        raise ExamError("Bu savol imtihonda yo'q")
    item.chosen_option = option


def grade_for(percent: float, grades: list[dict]) -> str:
    for g in sorted(grades, key=lambda g: -float(g.get("min_percent", 0))):
        if percent >= float(g.get("min_percent", 0)):
            return str(g.get("grade", ""))
    return "—"


@dataclass
class ExamResult:
    score: float
    max_score: float
    percent: float
    grade: str
    correct: int
    total: int
    items: list[ExamAnswer] = field(default_factory=list)


async def finish_exam(session: AsyncSession, exam: ExamSession, user: User) -> ExamResult:
    config = await session.get(ExamConfig, exam.config_id)
    items = await exam_items(session, exam)
    if exam.finished_at is None:
        now = utcnow()
        for item in items:
            q = await session.get(Question, item.question_id)
            item.is_correct = item.chosen_option == q.correct_option if item.chosen_option else False
            if item.chosen_option:  # javob berilganlari statistika va takrorlashga yoziladi
                session.add(Answer(user_id=user.id, question_id=q.id, chosen_option=item.chosen_option,
                                   is_correct=item.is_correct, source="exam", answered_at=now))
                await update_review(session, user.id, q.id, item.is_correct, now=now)
        if any(i.chosen_option for i in items):
            touch_streak(user)
        possible = sum(i.points for i in items) or 1
        earned = sum(i.points for i in items if i.is_correct)
        max_score = float(config.scoring.get("max_score", possible)) if config else possible
        exam.score = round(earned / possible * max_score, 1)
        exam.grade = grade_for(earned / possible * 100, config.grades if config else [])
        exam.finished_at = now
        await session.flush()

    max_score = float(config.scoring.get("max_score", 0)) if config else 0
    max_score = max_score or sum(i.points for i in items)
    percent = round(exam.score / max_score * 100, 1) if max_score else 0
    return ExamResult(score=exam.score, max_score=max_score, percent=percent, grade=exam.grade,
                      correct=sum(1 for i in items if i.is_correct), total=len(items), items=items)
