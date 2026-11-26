"""Admin panel API: savollar, import, davr/mavzular, "Tarixda bugun", xato xabarlari, imtihon formati."""
import asyncio
import csv
import io
from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, HTTPException, Request, UploadFile
from fastapi.responses import Response
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Integer, cast, distinct, func, or_, select
from sqlalchemy.orm import aliased

from app.api.deps import AdminUser, Session
from app.bot.broadcast import broadcast
from app.db import utcnow
from app.models import (
    Answer, Book, ExamAnswer, ExamConfig, Fact, HistoryEvent, Period, Question, QuestionReport, Referral, ReviewItem,
    Topic, User,
)
from app.services.daily import local_midnight_utc
from app.services.exam import get_active_config, rule_availability
from app.services.facts import VISIBLE as VISIBLE_FACTS
from app.services.facts_validation import clean_text
from app.services.facts_import import import_facts, read_csv as read_facts_csv
from app.services.question_gen import sync_questions
from app.services.importer import import_file, import_history_file
from app.services.media import MAX_IMAGE_BYTES, is_valid_image_url, save_image

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
    # Foydalanuvchilar eng ko‘p xato qiladigan mavzular (kamida 10 ta javob)
    ok_sum = func.sum(cast(Answer.is_correct, Integer))
    hard = (await session.execute(
        select(Topic.name, func.count(), ok_sum)
        .join(Question, Question.id == Answer.question_id).join(Topic, Topic.id == Question.topic_id)
        .group_by(Topic.id, Topic.name).having(func.count() >= 10)
        .order_by((ok_sum * 1.0 / func.count()).asc()).limit(5)
    )).all()
    inviter = aliased(User)
    top_inviters = (await session.execute(
        select(inviter.full_name, func.count(Referral.id), func.count(Referral.activated_at))
        .join(Referral, Referral.inviter_id == inviter.id)
        .group_by(inviter.id, inviter.full_name).order_by(func.count(Referral.activated_at).desc()).limit(5)
    )).all()
    return {
        "referrals": {
            "total": await count(Referral),
            "active": await count(Referral, Referral.activated_at.is_not(None)),
            "top": [{"name": n or "Foydalanuvchi", "invited": c, "active": a} for n, c, a in top_inviters],
        },
        "hard_topics": [{"name": n, "answers": c, "accuracy": round(100 * (k or 0) / c)} for n, c, k in hard],
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
        "fact_id": q.fact_id, "auto": bool(q.gen_key) and not q.gen_key.startswith("test:"), "locked": q.locked,
        "is_active": q.is_active, "image_url": q.image_url,
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
    image_url: str | None = Field(None, max_length=500)

    @field_validator("image_url")
    @classmethod
    def _image(cls, v: str | None) -> str | None:
        v = (v or "").strip() or None
        if v and not is_valid_image_url(v):
            raise ValueError("Rasm havolasi http(s):// bilan boshlanishi kerak")
        return v


async def reload_question(session, qid: int) -> Question:
    """Saqlangandan keyin savolni davr/mavzu nomlari bilan qayta o‘qiydi."""
    session.expunge_all()
    return await session.get(Question, qid)


def apply_question(q: Question, body: QuestionIn) -> None:
    # o‘/g‘ belgisi va qo'shtirnoqlar CLAUDE.md qoidasiga ko'ra tozalanadi
    q.text, q.option_a, q.option_b, q.option_c, q.option_d = (
        clean_text(body.text), clean_text(body.a), clean_text(body.b), clean_text(body.c), clean_text(body.d))
    q.correct_option, q.explanation, q.difficulty = body.correct, clean_text(body.explanation), body.difficulty
    q.period_id, q.topic_id, q.is_active = body.period_id, body.topic_id, body.is_active
    q.image_url = body.image_url


@router.get("/questions")
async def list_questions(
    _: AdminUser, session: Session, q: str = "", period_id: int | None = None, topic_id: int | None = None,
    difficulty: int | None = None, active: bool | None = None, page: int = 1, size: int = 20,
    source: str = "", sort: str = "",
) -> dict:
    """source: auto (faktlardan) | edited (admin tahrirlagan avtomatik) | manual (qo‘lda kiritilgan).
    sort=hard: o‘quvchilar eng ko‘p adashgan savollar (kamida 3 javob) — xato tuzilgan savolni topish uchun."""
    query = select(Question)
    auto = Question.gen_key.is_not(None) & Question.gen_key.not_like("test:%")
    if source == "auto":
        query = query.where(auto, Question.locked.is_(False))
    elif source == "edited":
        query = query.where(auto, Question.locked.is_(True))
    elif source == "manual":  # admin kiritgan + data/testlar/ fayllaridan
        query = query.where(~auto)
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
    size = max(1, min(size, 100))
    offset = (max(page, 1) - 1) * size
    if sort == "hard":
        n = func.count(Answer.id)
        wrong = func.sum(1 - cast(Answer.is_correct, Integer))
        st = (select(Answer.question_id.label("qid"), n.label("n"), wrong.label("wrong"))
              .group_by(Answer.question_id).having(n >= 3).subquery())
        query = query.join(st, st.c.qid == Question.id)
        total = await session.scalar(select(func.count()).select_from(query.subquery()))
        rows = (await session.execute(
            query.add_columns(st.c.n, st.c.wrong)
            .order_by((st.c.wrong * 1.0 / st.c.n).desc(), st.c.n.desc(), Question.id).offset(offset).limit(size)
        )).all()
        items = [{**q_out(x), "answers": cnt, "accuracy": round(100 * (cnt - (w or 0)) / cnt)} for x, cnt, w in rows]
        return {"total": total, "page": page, "size": size, "items": items}
    total = await session.scalar(select(func.count()).select_from(query.subquery()))
    rows = await session.scalars(query.order_by(Question.id.desc()).offset(offset).limit(size))
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
    if q.gen_key:
        q.locked = True  # faktlardan qayta tuzishda admin tahriri ustidan yozilmaydi
    await session.commit()
    return q_out(await reload_question(session, qid))


@router.delete("/questions/{qid}")
async def delete_question(qid: int, _: AdminUser, session: Session) -> dict:
    """Hech kim javob bermagan savol butunlay o‘chadi, aks holda faqat o‘chirib qo‘yiladi (statistika saqlanadi)."""
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


# ---------- Rasmlar ----------

@router.post("/media")
async def upload_media(file: UploadFile, _: AdminUser, session: Session) -> dict:
    data = await file.read(MAX_IMAGE_BYTES + 1)
    try:
        media = await save_image(session, data)
    except ValueError as e:
        raise HTTPException(400, str(e)) from None
    await session.commit()
    return {"url": f"/api/media/{media.id}"}


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
        ["savol", "a", "b", "c", "d", "togri", "izoh", "mavzu", "davr", "qiyinlik", "rasm"],
        [["Amir Temur qaysi yilda tug‘ilgan?", "1320", "1336", "1370", "1405", "B",
          "Amir Temur 1336-yil 9-aprelda tug‘ilgan.", "Amir Temur va Temuriylar", "O‘rta asrlar", "1", ""]],
    ),
    "history": (
        ["oy", "kun", "yil", "sarlavha", "matn"],
        [["4", "9", "1336", "Amir Temur tavalludi", "Amir Temur Kesh yaqinidagi Xo‘ja Ilg‘or qishlog‘ida tug‘ilgan."]],
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
        for col, width in zip("ABCDEFGHIJK", [50, 18, 18, 18, 18, 8, 50, 28, 18, 10, 30]):
            ws.column_dimensions[col].width = width
        buf = io.BytesIO()
        wb.save(buf)
        data, mime = buf.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return Response(data, media_type=mime,
                    headers={"Content-Disposition": f'attachment; filename="{kind}_shablon.{ext}"'})


# ---------- Eksport (zaxira nusxa) ----------

def _xlsx(title: str, headers: list[str], rows: list[list], widths: list[int]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = title
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="2E9E5B")
    for r in rows:
        ws.append(r)
    for i, w in enumerate(widths):
        ws.column_dimensions[chr(ord("A") + i)].width = w
    ws.freeze_panes = "A2"
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.get("/export/{kind}.xlsx")
async def export(kind: Literal["questions", "history"], _: AdminUser, session: Session) -> Response:
    """Import formatining o‘zida yuklab beradi — faylni tahrirlab, qayta import qilish mumkin."""
    if kind == "questions":
        qs = await session.scalars(select(Question).order_by(Question.id))
        rows = [[q.text, q.option_a, q.option_b, q.option_c, q.option_d, q.correct_option.upper(),
                 q.explanation, q.topic.name if q.topic else "", q.period.name if q.period else "",
                 q.difficulty, q.image_url or "", q.id, "ha" if q.is_active else "yo‘q"] for q in qs]
        data = _xlsx("Savollar", [*TEMPLATES["questions"][0], "id", "faol"], rows,
                     [50, 18, 18, 18, 18, 8, 50, 28, 18, 10, 30, 6, 6])
    else:
        es = await session.scalars(select(HistoryEvent).order_by(HistoryEvent.month, HistoryEvent.day))
        rows = [[e.month, e.day, e.year or "", e.title, e.text] for e in es]
        data = _xlsx("Voqealar", TEMPLATES["history"][0], rows, [6, 6, 8, 40, 80])
    name = f"{kind}_{utcnow():%Y-%m-%d}.xlsx"
    return Response(data, media_type=XLSX, headers={"Content-Disposition": f'attachment; filename="{name}"'})


# ---------- E’lon yuborish ----------

class BroadcastIn(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    audience: Literal["all", "active7", "active30"] = "all"


async def _recipients(session, audience: str) -> list[int]:
    q = select(User.telegram_id).where(User.is_blocked.is_(False))
    if audience != "all":
        days = 7 if audience == "active7" else 30
        active = select(Answer.user_id).where(Answer.answered_at >= utcnow() - timedelta(days=days))
        q = q.where(User.id.in_(active))
    return list(await session.scalars(q))


@router.get("/broadcast")
async def broadcast_status(_: AdminUser, request: Request, session: Session, audience: str = "all") -> dict:
    status = getattr(request.app.state, "broadcast", None) or {}
    return {"status": status, "recipients": len(await _recipients(session, audience)),
            "bot_ready": getattr(request.app.state, "bot", None) is not None}


@router.post("/broadcast")
async def broadcast_send(body: BroadcastIn, _: AdminUser, request: Request, session: Session) -> dict:
    bot = getattr(request.app.state, "bot", None)
    if bot is None:
        raise HTTPException(503, "Bot ishga tushmagan (ilovani python -m app.main orqali ishga tushiring)")
    status = getattr(request.app.state, "broadcast", None)
    if status and status.get("running"):
        raise HTTPException(409, "Oldingi e’lon hali yuborilmoqda")
    recipients = await _recipients(session, body.audience)
    status = {"total": len(recipients), "sent": 0, "failed": 0, "running": True, "started_at": utcnow().isoformat() + "Z"}
    request.app.state.broadcast = status
    # Fon rejimida yuboramiz — admin sahifani yopsa ham davom etadi
    request.app.state.broadcast_task = asyncio.create_task(broadcast(bot, recipients, body.text.strip(), status))
    return {"queued": len(recipients)}


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
        raise HTTPException(400, "Bu davrda savollar bor. Avval savollarni boshqa davrga o‘tkazing")
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
        raise HTTPException(400, "Bu mavzuda savollar bor. Avval ularni boshqa mavzuga o‘tkazing")
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


# ---------- Faktlar bazasi ----------

def fact_out(f: Fact) -> dict:
    return {
        "id": f.id, "tur": f.tur, "nom": f.nom, "matn": f.matn, "sana_matn": f.sana_matn,
        "yil_boshi": f.yil_boshi, "yil_oxiri": f.yil_oxiri, "asr": f.asr, "davr": f.davr, "hudud": f.hudud,
        "sinf": f.sinf, "book_id": f.book_id, "source": f.source, "mavzu_nomi": f.mavzu_nomi,
        "iqtibos": f.iqtibos, "shaxs_faoliyati": f.shaxs_faoliyati, "shaxs_ishoralar": f.shaxs_ishoralar,
        "urush_tomonlari": f.urush_tomonlari, "golib": f.golib, "natija": f.natija,
        "joy_turi": f.joy_turi, "joy_hozirgi": f.joy_hozirgi, "asar_muallifi": f.asar_muallifi,
        "ishonch": f.ishonch, "izoh": f.izoh, "flags": f.flags,
        "hidden_import": f.hidden_import, "hidden_admin": f.hidden_admin, "visible": f.visible,
    }


@router.get("/facts/summary")
async def facts_summary(_: AdminUser, session: Session) -> dict:
    by_type = dict((await session.execute(select(Fact.tur, func.count()).group_by(Fact.tur))).all())
    by_davr = dict((await session.execute(select(Fact.davr, func.count()).group_by(Fact.davr))).all())
    flags: dict[str, int] = {}
    for fl in await session.scalars(select(Fact.flags)):
        for f in fl or []:
            flags[f] = flags.get(f, 0) + 1
    books = [
        {"id": b.id, "title": b.title, "sinf": b.sinf, "fan": b.fan, "count": c}
        for b, c in (await session.execute(
            select(Book, func.count(Fact.id)).join(Fact, Fact.book_id == Book.id)
            .group_by(Book.id).order_by(Book.sinf, Book.fan)
        )).all()
    ]
    return {
        "total": sum(by_type.values()),
        "visible": await session.scalar(select(func.count()).select_from(Fact).where(VISIBLE_FACTS)),
        "hidden_admin": await session.scalar(select(func.count()).select_from(Fact).where(Fact.hidden_admin.is_(True))),
        "by_type": by_type, "by_davr": by_davr, "flags": flags, "books": books,
    }


@router.get("/facts")
async def list_facts(
    _: AdminUser, session: Session, q: str = "", tur: str = "", davr: str = "", hudud: str = "",
    book_id: str = "", flag: str = "", hidden: bool | None = None, page: int = 1, size: int = 30,
) -> dict:
    query = select(Fact)
    if q:
        like = f"%{q}%"
        query = query.where(or_(Fact.nom.ilike(like), Fact.matn.ilike(like), Fact.id.ilike(like)))
    for col, val in ((Fact.tur, tur), (Fact.davr, davr), (Fact.hudud, hudud), (Fact.book_id, book_id)):
        if val:
            query = query.where(col == val)
    if hidden is True:
        query = query.where(~VISIBLE_FACTS)
    elif hidden is False:
        query = query.where(VISIBLE_FACTS)
    rows = list(await session.scalars(query.order_by(Fact.id)))
    if flag:  # JSON ro‘yxat bo‘yicha filtr — bazadan mustaqil bo‘lishi uchun Python’da
        rows = [f for f in rows if flag in (f.flags or [])]
    size = max(1, min(size, 100))
    start = (max(page, 1) - 1) * size
    return {"total": len(rows), "page": page, "size": size, "items": [fact_out(f) for f in rows[start:start + size]]}


class FactVisibilityIn(BaseModel):
    hidden_admin: bool


@router.patch("/facts/{fact_id}")
async def set_fact_visibility(fact_id: str, body: FactVisibilityIn, _: AdminUser, session: Session) -> dict:
    fact = await session.get(Fact, fact_id)
    if fact is None:
        raise HTTPException(404, "Fakt topilmadi")
    fact.hidden_admin = body.hidden_admin
    await session.commit()
    return fact_out(fact)


@router.post("/import/facts")
async def import_facts_file(file: UploadFile, _: AdminUser, session: Session, dry_run: bool = False) -> dict:
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(400, "Faktlar bazasi .csv (UTF-8) formatida bo‘lishi kerak")
    content = await file.read(20 * 1024 * 1024 + 1)
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(413, "Fayl 20 MB dan katta")
    try:
        report = await import_facts(session, read_facts_csv(content), dry_run=dry_run)
    except (ValueError, UnicodeDecodeError) as e:
        raise HTTPException(400, f"CSV o‘qilmadi: {e}") from None
    if not dry_run:
        # Faktlar o'zgardi — test savollari ham qayta tuziladi (admin tahrirlaganlari saqlanadi)
        questions = await sync_questions(session)
        await session.commit()
        return {**report.as_dict(), "questions": questions.as_dict()}
    return report.as_dict()
