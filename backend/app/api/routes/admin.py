"""Admin panel API: savollar, import, davr/mavzular, "Tarixda bugun", xato xabarlari, imtihon formati."""
import csv
import io
from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import Response
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from pydantic import BaseModel, Field
from sqlalchemy import Integer, cast, distinct, func, or_, select

from app.api.deps import AdminUser, Session
from app.db import utcnow
from app.models import (
    Answer, ExamAnswer, ExamConfig, HistoryEvent, Period, Question, QuestionReport, ReviewItem, Topic, User,
)
from app.services.daily import local_midnight_utc
from app.services.exam import get_active_config, rule_availability
from app.services.importer import import_file, import_history_file

router = APIRouter(prefix="/api/admin")
MAX_UPLOAD = 10 * 1024 * 1024


# ---------- Statistika ----------

@router.get("/stats")
async def stats(_: AdminUser, session: Session) -> dict:
    count = lambda m, *w: session.scalar(select(func.count()).select_from(m).where(*w))  # noqa: E731
    week_ago = utcnow() - timedelta(days=7)
    by_difficulty = dict((await session.execute(
        select(Question.difficulty, func.count()).where(Question.is_active.is_(True)).group_by(Question.difficulty)
    )).all())
    by_period = (await session.execute(
        select(func.coalesce(Period.name, "Davrsiz"), func.count(Question.id))
        .select_from(Question).outerjoin(Period, Period.id == Question.period_id)
        .where(Question.is_active.is_(True)).group_by(Period.name)
    )).all()
    accuracy = (await session.execute(
        select(func.count(), func.coalesce(func.sum(cast(Answer.is_correct, Integer)), 0))
    )).one()
    return {
        "users": await count(User),
        "active_week": await session.scalar(
            select(func.count(distinct(Answer.user_id))).where(Answer.answered_at >= week_ago)),
        "questions": await count(Question, Question.is_active.is_(True)),
        "questions_inactive": await count(Question, Question.is_active.is_(False)),
        "answers_today": await count(Answer, Answer.answered_at >= local_midnight_utc()),
        "answers_total": accuracy[0],
        "accuracy": round(100 * accuracy[1] / accuracy[0]) if accuracy[0] else 0,
        "reports_new": await count(QuestionReport, QuestionReport.status == "new"),
        "history_events": await count(HistoryEvent),
        "by_difficulty": {str(k): v for k, v in by_difficulty.items()},
        "by_period": [{"name": n, "count": c} for n, c in by_period],
    }


# ---------- Savollar ----------

def q_out(q: Question) -> dict:
    return {
        "id": q.id, "text": q.text, "a": q.option_a, "b": q.option_b, "c": q.option_c, "d": q.option_d,
        "correct": q.correct_option, "explanation": q.explanation, "difficulty": q.difficulty,
        "period_id": q.period_id, "topic_id": q.topic_id,
        "period": q.period.name if q.period else None, "topic": q.topic.name if q.topic else None,
        "is_active": q.is_active,
    }


class QuestionIn(BaseModel):
    text: str = Field(min_length=3)
    a: str = Field(min_length=1)
    b: str = Field(min_length=1)
    c: str = Field(min_length=1)
    d: str = Field(min_length=1)
    correct: Literal["a", "b", "c", "d"]
    explanation: str = ""
    difficulty: int = Field(1, ge=1, le=3)
    period_id: int | None = None
    topic_id: int | None = None
    is_active: bool = True


async def reload_question(session, qid: int) -> Question:
    """Saqlangandan keyin savolni davr/mavzu nomlari bilan qayta o'qiydi."""
    session.expunge_all()
    return await session.get(Question, qid)


def apply_question(q: Question, body: QuestionIn) -> None:
    q.text, q.option_a, q.option_b, q.option_c, q.option_d = (
        body.text.strip(), body.a.strip(), body.b.strip(), body.c.strip(), body.d.strip())
    q.correct_option, q.explanation, q.difficulty = body.correct, body.explanation.strip(), body.difficulty
    q.period_id, q.topic_id, q.is_active = body.period_id, body.topic_id, body.is_active


@router.get("/questions")
async def list_questions(
    _: AdminUser, session: Session, q: str = "", period_id: int | None = None, topic_id: int | None = None,
    difficulty: int | None = None, active: bool | None = None, page: int = 1, size: int = 20,
) -> dict:
    query = select(Question)
    if q:
        like = f"%{q}%"
        query = query.where(or_(Question.text.ilike(like), Question.explanation.ilike(like),
                                *(getattr(Question, f"option_{o}").ilike(like) for o in "abcd")))
    if period_id:
        query = query.where(Question.period_id == period_id)
    if topic_id:
        query = query.where(Question.topic_id == topic_id)
    if difficulty:
        query = query.where(Question.difficulty == difficulty)
    if active is not None:
        query = query.where(Question.is_active.is_(active))
    total = await session.scalar(select(func.count()).select_from(query.subquery()))
    size = max(1, min(size, 100))
    rows = await session.scalars(query.order_by(Question.id.desc()).offset((max(page, 1) - 1) * size).limit(size))
    return {"total": total, "page": page, "size": size, "items": [q_out(x) for x in rows]}


@router.post("/questions")
async def create_question(body: QuestionIn, _: AdminUser, session: Session) -> dict:
    q = Question()
    apply_question(q, body)
    session.add(q)
    await session.commit()
    return q_out(await reload_question(session, q.id))


@router.put("/questions/{qid}")
async def update_question(qid: int, body: QuestionIn, _: AdminUser, session: Session) -> dict:
    q = await session.get(Question, qid)
    if q is None:
        raise HTTPException(404, "Savol topilmadi")
    apply_question(q, body)
    await session.commit()
    return q_out(await reload_question(session, qid))


@router.delete("/questions/{qid}")
async def delete_question(qid: int, _: AdminUser, session: Session) -> dict:
    """Hech kim javob bermagan savol butunlay o'chadi, aks holda faqat o'chirib qo'yiladi (statistika saqlanadi)."""
    q = await session.get(Question, qid)
    if q is None:
        raise HTTPException(404, "Savol topilmadi")
    used = any([
        await session.scalar(select(func.count()).select_from(m).where(m.question_id == qid))
        for m in (Answer, ExamAnswer, QuestionReport, ReviewItem)
    ])
    if used:
        q.is_active = False
    else:
        await session.delete(q)
    await session.commit()
    return {"deleted": not used, "deactivated": used}


# ---------- Import va shablonlar ----------

async def _read_upload(file: UploadFile) -> bytes:
    content = await file.read()
    if len(content) > MAX_UPLOAD:
        raise HTTPException(413, "Fayl 10 MB dan katta")
    return content


@router.post("/import/questions")
async def import_questions(file: UploadFile, _: AdminUser, session: Session) -> dict:
    try:
        report = await import_file(session, file.filename or "", await _read_upload(file))
    except ValueError as e:
        raise HTTPException(400, str(e)) from None
    await session.commit()
    return report.__dict__


@router.post("/import/history")
async def import_history(file: UploadFile, _: AdminUser, session: Session) -> dict:
    try:
        report = await import_history_file(session, file.filename or "", await _read_upload(file))
    except ValueError as e:
        raise HTTPException(400, str(e)) from None
    await session.commit()
    return report.__dict__


TEMPLATES = {
    "questions": (
        ["savol", "a", "b", "c", "d", "togri", "izoh", "mavzu", "davr", "qiyinlik"],
        [["Amir Temur qaysi yilda tug'ilgan?", "1320", "1336", "1370", "1405", "B",
          "Amir Temur 1336-yil 9-aprelda tug'ilgan.", "Amir Temur va Temuriylar", "O'rta asrlar", "1"]],
    ),
    "history": (
        ["oy", "kun", "yil", "sarlavha", "matn"],
        [["4", "9", "1336", "Amir Temur tavalludi", "Amir Temur Kesh yaqinidagi Xo'ja Ilg'or qishlog'ida tug'ilgan."]],
    ),
}


@router.get("/template/{kind}.{ext}")
async def template(kind: Literal["questions", "history"], ext: Literal["xlsx", "csv"], _: AdminUser) -> Response:
    headers, rows = TEMPLATES[kind]
    if ext == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(headers)
        writer.writerows(rows)
        data, mime = ("﻿" + buf.getvalue()).encode(), "text/csv; charset=utf-8"
    else:
        wb = Workbook()
        ws = wb.active
        ws.title = "Savollar" if kind == "questions" else "Voqealar"
        ws.append(headers)
        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="2E9E5B")
        for r in rows:
            ws.append(r)
        for col, width in zip("ABCDEFGHIJ", [50, 18, 18, 18, 18, 8, 50, 28, 18, 10]):
            ws.column_dimensions[col].width = width
        buf = io.BytesIO()
        wb.save(buf)
        data, mime = buf.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return Response(data, media_type=mime,
                    headers={"Content-Disposition": f'attachment; filename="{kind}_shablon.{ext}"'})


# ---------- Davrlar va mavzular ----------

class PeriodIn(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    sort_order: int = 0


class TopicIn(PeriodIn):
    period_id: int | None = None


@router.get("/periods")
async def periods(_: AdminUser, session: Session) -> list[dict]:
    counts = dict((await session.execute(
        select(Question.topic_id, func.count()).where(Question.is_active.is_(True)).group_by(Question.topic_id)
    )).all())
    pcounts = dict((await session.execute(
        select(Question.period_id, func.count()).where(Question.is_active.is_(True)).group_by(Question.period_id)
    )).all())
    topics = list(await session.scalars(select(Topic).order_by(Topic.sort_order, Topic.id)))
    return [
        {"id": p.id, "name": p.name, "sort_order": p.sort_order, "questions": pcounts.get(p.id, 0),
         "topics": [{"id": t.id, "name": t.name, "sort_order": t.sort_order, "period_id": t.period_id,
                     "questions": counts.get(t.id, 0)} for t in topics if t.period_id == p.id]}
        for p in await session.scalars(select(Period).order_by(Period.sort_order, Period.id))
    ]


@router.post("/periods")
async def create_period(body: PeriodIn, _: AdminUser, session: Session) -> dict:
    if await session.scalar(select(Period).where(Period.name == body.name.strip())):
        raise HTTPException(400, "Bunday davr bor")
    p = Period(name=body.name.strip(), sort_order=body.sort_order)
    session.add(p)
    await session.commit()
    return {"id": p.id}


@router.put("/periods/{pid}")
async def update_period(pid: int, body: PeriodIn, _: AdminUser, session: Session) -> dict:
    p = await session.get(Period, pid)
    if p is None:
        raise HTTPException(404, "Topilmadi")
    p.name, p.sort_order = body.name.strip(), body.sort_order
    await session.commit()
    return {"ok": True}


@router.delete("/periods/{pid}")
async def delete_period(pid: int, _: AdminUser, session: Session) -> dict:
    p = await session.get(Period, pid)
    if p is None:
        raise HTTPException(404, "Topilmadi")
    if await session.scalar(select(func.count()).select_from(Question).where(Question.period_id == pid)):
        raise HTTPException(400, "Bu davrda savollar bor. Avval savollarni boshqa davrga o'tkazing")
    for t in await session.scalars(select(Topic).where(Topic.period_id == pid)):
        if await session.scalar(select(func.count()).select_from(Question).where(Question.topic_id == t.id)):
            raise HTTPException(400, "Bu davr mavzularida savollar bor")
        await session.delete(t)
    await session.delete(p)
    await session.commit()
    return {"ok": True}


@router.post("/topics")
async def create_topic(body: TopicIn, _: AdminUser, session: Session) -> dict:
    t = Topic(name=body.name.strip(), sort_order=body.sort_order, period_id=body.period_id)
    session.add(t)
    await session.commit()
    return {"id": t.id}


@router.put("/topics/{tid}")
async def update_topic(tid: int, body: TopicIn, _: AdminUser, session: Session) -> dict:
    t = await session.get(Topic, tid)
    if t is None:
        raise HTTPException(404, "Topilmadi")
    t.name, t.sort_order, t.period_id = body.name.strip(), body.sort_order, body.period_id
    await session.commit()
    return {"ok": True}


@router.delete("/topics/{tid}")
async def delete_topic(tid: int, _: AdminUser, session: Session) -> dict:
    t = await session.get(Topic, tid)
    if t is None:
        raise HTTPException(404, "Topilmadi")
    if await session.scalar(select(func.count()).select_from(Question).where(Question.topic_id == tid)):
        raise HTTPException(400, "Bu mavzuda savollar bor. Avval ularni boshqa mavzuga o'tkazing")
    await session.delete(t)
    await session.commit()
    return {"ok": True}


# ---------- "Tarixda bugun" ----------

class HistoryIn(BaseModel):
    month: int = Field(ge=1, le=12)
    day: int = Field(ge=1, le=31)
    year: int | None = None
    title: str = Field(min_length=1, max_length=255)
    text: str = ""


def h_out(e: HistoryEvent) -> dict:
    return {"id": e.id, "month": e.month, "day": e.day, "year": e.year, "title": e.title, "text": e.text}


@router.get("/history")
async def list_history(_: AdminUser, session: Session, month: int | None = None) -> list[dict]:
    q = select(HistoryEvent).order_by(HistoryEvent.month, HistoryEvent.day, HistoryEvent.year)
    if month:
        q = q.where(HistoryEvent.month == month)
    return [h_out(e) for e in await session.scalars(q)]


@router.post("/history")
async def create_history(body: HistoryIn, _: AdminUser, session: Session) -> dict:
    e = HistoryEvent(**body.model_dump())
    session.add(e)
    await session.commit()
    return h_out(e)


@router.put("/history/{eid}")
async def update_history(eid: int, body: HistoryIn, _: AdminUser, session: Session) -> dict:
    e = await session.get(HistoryEvent, eid)
    if e is None:
        raise HTTPException(404, "Topilmadi")
    for k, v in body.model_dump().items():
        setattr(e, k, v)
    await session.commit()
    return h_out(e)


@router.delete("/history/{eid}")
async def delete_history(eid: int, _: AdminUser, session: Session) -> dict:
    e = await session.get(HistoryEvent, eid)
    if e is None:
        raise HTTPException(404, "Topilmadi")
    await session.delete(e)
    await session.commit()
    return {"ok": True}


# ---------- Xato xabarlari ----------

@router.get("/reports")
async def list_reports(_: AdminUser, session: Session, status: str = "new") -> list[dict]:
    rows = await session.scalars(
        select(QuestionReport).where(QuestionReport.status == status)
        .order_by(QuestionReport.created_at.desc()).limit(200)
    )
    return [{
        "id": r.id, "comment": r.comment, "status": r.status,
        "created_at": r.created_at.isoformat() + "Z",
        "user": r.user.full_name, "question": q_out(r.question),
    } for r in rows]


class ResolveIn(BaseModel):
    status: Literal["fixed", "rejected", "new"]
    deactivate: bool = False


@router.post("/reports/{rid}")
async def resolve_report(rid: int, body: ResolveIn, _: AdminUser, session: Session) -> dict:
    r = await session.get(QuestionReport, rid)
    if r is None:
        raise HTTPException(404, "Topilmadi")
    r.status = body.status
    if body.deactivate:
        r.question.is_active = False
    await session.commit()
    return {"ok": True}


# ---------- Imtihon formati ----------

class RuleIn(BaseModel):
    count: int = Field(ge=1, le=500)
    points: float = Field(1.0, gt=0)
    difficulty: int | None = Field(None, ge=1, le=3)
    period: str | None = None
    topic: str | None = None


class GradeIn(BaseModel):
    min_percent: float = Field(ge=0, le=100)
    grade: str = Field(min_length=1, max_length=16)


class ExamConfigIn(BaseModel):
    name: str = Field(min_length=1)
    duration_minutes: int = Field(ge=1, le=600)
    max_score: float = Field(gt=0)
    rules: list[RuleIn] = Field(min_length=1)
    grades: list[GradeIn] = Field(min_length=1)


async def _config_out(session, c: ExamConfig) -> dict:
    return {
        "id": c.id, "name": c.name, "duration_minutes": c.duration_minutes,
        "max_score": c.scoring.get("max_score", 100), "rules": c.rules, "grades": c.grades,
        "availability": await rule_availability(session, c.rules),
    }


@router.get("/exam-config")
async def get_exam_config(_: AdminUser, session: Session) -> dict | None:
    c = await get_active_config(session)
    return await _config_out(session, c) if c else None


@router.put("/exam-config")
async def save_exam_config(body: ExamConfigIn, _: AdminUser, session: Session) -> dict:
    c = await get_active_config(session)
    if c is None:
        c = ExamConfig(is_active=True)
        session.add(c)
    c.name, c.duration_minutes = body.name, body.duration_minutes
    c.scoring = {"max_score": body.max_score}
    c.rules = [r.model_dump(exclude_none=True) for r in body.rules]
    c.grades = sorted((g.model_dump() for g in body.grades), key=lambda g: -g["min_percent"])
    await session.commit()
    return await _config_out(session, c)
