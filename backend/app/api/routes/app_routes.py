"""Mini App uchun API (foydalanuvchi tomoni).

Barcha matnlar foydalanuvchi alifbosida (lotin/kirill) qaytariladi.
"""
from datetime import UTC, time, timedelta
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.deps import CurrentUser, Session
from app.config import settings
from app.db import local_today, utcnow
from app.models import Answer, ExamConfig, ExamSession, LessonSession, Question, User
from app.services import exam as exam_service
from app.services.daily import answers_today, daily_question_ids
from app.services.history import events_for
from app.services.quiz import (
    REPORTS_PER_DAY, create_report, get_question, pick_question_ids, record_answer, reports_last_day,
)
from app.services.rating import user_rank, user_week_xp, weekly_leaderboard, xp_for
from app.services.review import due_count, due_question_ids
from app.services.stats import answer_totals, learning_path
from app.services.streak import effective_streak
from app.services.translit import tr

router = APIRouter(prefix="/api")
Option = Literal["a", "b", "c", "d"]


def iso(dt) -> str:
    return dt.replace(tzinfo=UTC).isoformat().replace("+00:00", "Z")


def question_out(q: Question, a: str, chosen: str | None = None) -> dict:
    data = {
        "id": q.id,
        "text": tr(q.text, a),
        "options": [{"key": k, "text": tr(v, a)} for k, v in q.options.items()],
        "period": tr(q.period.name, a) if q.period else None,
        "topic": tr(q.topic.name, a) if q.topic else None,
        "difficulty": q.difficulty,
        "image": q.image_url,
    }
    if chosen is not None:
        data["chosen"] = chosen
    return data


# ---------- Bosh sahifa va profil ----------

async def week_activity(session, user: User) -> list[dict]:
    """Oxirgi 7 kun: qaysi kunlari faol bo'lgan (ketma-ketlik kalendari uchun)."""
    today = local_today()
    since = utcnow() - timedelta(days=8)
    times = await session.scalars(
        select(Answer.answered_at).where(Answer.user_id == user.id, Answer.answered_at >= since)
    )
    active = {t.replace(tzinfo=UTC).astimezone(settings.tz).date() for t in times}
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    return [{"date": d.isoformat(), "weekday": d.weekday(), "active": d in active} for d in days]


@router.get("/home")
async def home(user: CurrentUser, session: Session) -> dict:
    a = user.alphabet
    total, correct = await answer_totals(session, user.id)
    path = await learning_path(session, user)
    for p in path:
        p["name"] = tr(p["name"], a)
        for t_ in p["topics"]:
            t_["name"] = tr(t_["name"], a)
    config = await exam_service.get_active_config(session)
    events = await events_for(session)
    return {
        "user": {
            "name": user.full_name, "alphabet": a, "is_admin": user.is_admin,
            "alphabet_chosen": user.alphabet_chosen,
            "streak": effective_streak(user), "streak_best": user.streak_best,
            "reminder_enabled": user.reminder_enabled,
            "reminder_time": user.reminder_time.strftime("%H:%M"),
        },
        "today": {"done": await answers_today(session, user.id), "goal": settings.daily_question_count},
        "week": {"xp": await user_week_xp(session, user.id), "rank": await user_rank(session, user.id),
                 "days": await week_activity(session, user)},
        "totals": {"answers": total, "correct": correct},
        "due_count": await due_count(session, user.id),
        "path": path,
        "exam": {
            "name": tr(config.name, a), "count": await exam_service.expected_questions(session, config),
            "minutes": config.duration_minutes,
        } if config else None,
        "history_today": [
            {"year": e.year, "title": tr(e.title, a), "text": tr(e.text, a)} for e in events
        ],
    }


class MeUpdate(BaseModel):
    alphabet: Literal["latn", "cyrl"] | None = None
    reminder_enabled: bool | None = None
    reminder_time: str | None = Field(None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")


@router.patch("/me")
async def update_me(body: MeUpdate, user: CurrentUser, session: Session) -> dict:
    if body.alphabet:
        user.alphabet = body.alphabet
        user.alphabet_chosen = True
    if body.reminder_enabled is not None:
        user.reminder_enabled = body.reminder_enabled
    if body.reminder_time:
        h, m = map(int, body.reminder_time.split(":"))
        user.reminder_time = time(h, m)
        user.last_reminder_date = None
    await session.commit()
    return {"ok": True}


# ---------- Darslar (mashq) ----------

class LessonIn(BaseModel):
    mode: Literal["mixed", "period", "topic", "daily", "review"]
    id: int | None = None


@router.post("/lessons")
async def start_lesson(body: LessonIn, user: CurrentUser, session: Session) -> dict:
    n = settings.quiz_length
    if body.mode == "daily":
        ids = await daily_question_ids(session, user.id)
    elif body.mode == "review":
        ids = await due_question_ids(session, user.id, n)
    elif body.mode == "period":
        ids = await pick_question_ids(session, n, period_id=body.id)
    elif body.mode == "topic":
        ids = await pick_question_ids(session, n, topic_id=body.id)
    else:
        ids = await pick_question_ids(session, n)
    questions = [q for q in [await get_question(session, i) for i in ids] if q]
    source = body.mode if body.mode in ("daily", "review") else "practice"
    lesson = LessonSession(user_id=user.id, source=source, question_ids=[q.id for q in questions])
    session.add(lesson)
    await session.commit()
    return {"lesson_id": lesson.id, "source": source,
            "questions": [question_out(q, user.alphabet) for q in questions]}


LESSON_TTL = timedelta(hours=24)


class AnswerIn(BaseModel):
    lesson_id: int
    question_id: int
    option: Option


@router.post("/answers")
async def answer(body: AnswerIn, user: CurrentUser, session: Session) -> dict:
    lesson = await session.get(LessonSession, body.lesson_id)
    if lesson is None or lesson.user_id != user.id or utcnow() - lesson.created_at > LESSON_TTL:
        raise HTTPException(404, "Dars topilmadi yoki eskirgan. Yangi dars boshlang")
    if body.question_id not in lesson.question_ids:
        raise HTTPException(400, "Bu savol ushbu darsda yo'q")
    if body.question_id in lesson.answered_ids:
        raise HTTPException(409, "Bu savolga allaqachon javob berilgan")
    q = await get_question(session, body.question_id)
    if q is None:
        raise HTTPException(404, "Savol topilmadi")
    lesson.answered_ids = [*lesson.answered_ids, q.id]  # yangi ro'yxat — SQLAlchemy o'zgarishni ko'radi
    result = await record_answer(session, user, q, body.option, source=lesson.source)
    done = await answers_today(session, user.id)
    await session.commit()
    goal = settings.daily_question_count
    return {
        "is_correct": result.is_correct,
        "correct_option": q.correct_option,
        "explanation": tr(q.explanation, user.alphabet),
        "xp": xp_for(result.is_correct),
        "streak": user.streak_current,
        "streak_increased": result.streak_increased,
        "today_done": done, "goal": goal, "goal_reached": done == goal,
    }


class ReportIn(BaseModel):
    question_id: int
    comment: str = Field(min_length=1, max_length=2000)


@router.post("/reports")
async def report(body: ReportIn, user: CurrentUser, session: Session, request: Request) -> dict:
    if await reports_last_day(session, user.id) >= REPORTS_PER_DAY:
        raise HTTPException(429, "Bugun juda ko'p xabar yubordingiz. Ertaga urinib ko'ring")
    q = await get_question(session, body.question_id)
    if q is None:
        raise HTTPException(404, "Savol topilmadi")
    rep = await create_report(session, user, q.id, body.comment)
    await session.commit()
    bot = getattr(request.app.state, "bot", None)
    if bot is not None:
        from app.bot.handlers.report import notify_admins
        await notify_admins(bot, rep, q, user)
    return {"ok": True}


# ---------- Reyting ----------

@router.get("/rating")
async def rating(user: CurrentUser, session: Session) -> dict:
    rows = await weekly_leaderboard(session, limit=50)
    return {
        "rows": [{"rank": r.rank, "name": r.name, "xp": r.xp, "is_me": r.user_id == user.id} for r in rows],
        "me": {"rank": await user_rank(session, user.id), "xp": await user_week_xp(session, user.id)},
    }


# ---------- Imtihon ----------

async def _exam_payload(session, exam: ExamSession, user: User) -> dict:
    config = await session.get(ExamConfig, exam.config_id)
    items = await exam_service.exam_items(session, exam)
    questions = [question_out(await get_question(session, i.question_id), user.alphabet, i.chosen_option or "")
                 for i in items]
    return {
        "id": exam.id, "name": tr(config.name, user.alphabet) if config else "",
        "deadline": iso(exam.deadline_at), "now": iso(utcnow()), "questions": questions,
    }


@router.get("/exam")
async def exam_info(user: CurrentUser, session: Session) -> dict:
    config = await exam_service.get_active_config(session)
    open_exam = await exam_service.get_open_exam(session, user)
    await session.commit()
    past = await session.scalars(
        select(ExamSession).where(ExamSession.user_id == user.id, ExamSession.finished_at.is_not(None))
        .order_by(ExamSession.id.desc()).limit(10)
    )
    max_score = float(config.scoring.get("max_score", 0)) if config else 0
    return {
        "config": {
            "name": tr(config.name, user.alphabet), "count": await exam_service.expected_questions(session, config),
            "minutes": config.duration_minutes, "max_score": max_score,
            "grades": config.grades,
        } if config else None,
        "open_exam_id": open_exam.id if open_exam else None,
        "history": [{"id": e.id, "date": iso(e.finished_at), "score": e.score, "grade": e.grade} for e in past],
    }


@router.post("/exam/start")
async def exam_start(user: CurrentUser, session: Session) -> dict:
    try:
        exam = await exam_service.start_exam(session, user)
    except exam_service.ExamError as e:
        raise HTTPException(400, str(e)) from None
    await session.commit()
    return await _exam_payload(session, exam, user)


async def _get_own_exam(session, exam_id: int, user: User) -> ExamSession:
    exam = await session.get(ExamSession, exam_id)
    if exam is None or exam.user_id != user.id:
        raise HTTPException(404, "Imtihon topilmadi")
    return exam


class ExamAnswerIn(BaseModel):
    question_id: int
    option: Option


@router.put("/exam/{exam_id}/answer")
async def exam_answer(exam_id: int, body: ExamAnswerIn, user: CurrentUser, session: Session) -> dict:
    exam = await _get_own_exam(session, exam_id, user)
    try:
        await exam_service.save_answer(session, exam, body.question_id, body.option)
    except exam_service.ExamError as e:
        raise HTTPException(409, str(e)) from None
    await session.commit()
    return {"ok": True}


@router.post("/exam/{exam_id}/finish")
async def exam_finish(exam_id: int, user: CurrentUser, session: Session) -> dict:
    exam = await _get_own_exam(session, exam_id, user)
    result = await exam_service.finish_exam(session, exam, user)
    await session.commit()
    a = user.alphabet
    items = []
    for i in result.items:
        q = await get_question(session, i.question_id)
        items.append({
            **question_out(q, a, i.chosen_option or ""),
            "correct_option": q.correct_option, "is_correct": bool(i.is_correct),
            "explanation": tr(q.explanation, a), "points": i.points,
        })
    return {
        "score": result.score, "max_score": result.max_score, "percent": result.percent,
        "grade": result.grade, "correct": result.correct, "total": result.total, "items": items,
    }
