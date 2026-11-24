"""Savollarni Excel (.xlsx) yoki CSV fayldan import qilish.

Fayl birinchi qatorida ustun nomlari bo'lishi kerak:
    savol | a | b | c | d | togri | izoh | mavzu | davr | qiyinlik

- togri: A, B, C yoki D
- qiyinlik: 1/2/3 yoki oson/o'rta/qiyin (bo'sh bo'lsa — 1)
- mavzu va davr bazada bo'lmasa, avtomatik yaratiladi
- matni bir xil savol ikkinchi marta qo'shilmaydi
"""
import csv
import io
from dataclasses import dataclass, field

from openpyxl import load_workbook
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OPTIONS, Period, Question, Topic

# Ustun nomlarining turli yozilishlari -> ichki nom
HEADER_ALIASES = {
    "savol": "text", "question": "text", "matn": "text",
    "a": "a", "b": "b", "c": "c", "d": "d",
    "variant a": "a", "variant b": "b", "variant c": "c", "variant d": "d",
    "togri": "correct", "togri javob": "correct", "javob": "correct", "correct": "correct",
    "izoh": "explanation", "explanation": "explanation",
    "mavzu": "topic", "topic": "topic",
    "davr": "period", "period": "period",
    "qiyinlik": "difficulty", "difficulty": "difficulty", "daraja": "difficulty",
}
REQUIRED = ("text", "a", "b", "c", "d", "correct")
DIFFICULTY_WORDS = {"oson": 1, "orta": 2, "qiyin": 3}


def _norm(value) -> str:
    return "" if value is None else str(value).strip()


def _key(value: str) -> str:
    """Ustun nomini solishtirish uchun: kichik harf, tutuq belgilarisiz."""
    v = _norm(value).lower()
    for ch in "'ʻʼ‘’`":
        v = v.replace(ch, "")
    return " ".join(v.split())


@dataclass
class ImportReport:
    added: int = 0
    skipped_duplicates: int = 0
    errors: list[str] = field(default_factory=list)


def read_rows(filename: str, content: bytes) -> list[dict[str, str]]:
    """Faylni o'qib, har bir qatorni {ichki_nom: qiymat} lug'atiga aylantiradi."""
    name = filename.lower()
    if name.endswith(".xlsx"):
        wb = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        raw = [list(r) for r in wb.active.iter_rows(values_only=True)]
    elif name.endswith(".csv"):
        text = content.decode("utf-8-sig")
        try:
            dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        raw = list(csv.reader(io.StringIO(text), dialect))
    else:
        raise ValueError("Faqat .xlsx yoki .csv fayl qabul qilinadi")

    if not raw:
        return []
    headers = [HEADER_ALIASES.get(_key(h)) for h in raw[0]]
    missing = [r for r in REQUIRED if r not in headers]
    if missing:
        raise ValueError("Ustunlar topilmadi: " + ", ".join(missing))

    rows = []
    for values in raw[1:]:
        row = {h: _norm(v) for h, v in zip(headers, values) if h}
        if any(row.values()):
            rows.append(row)
    return rows


def _difficulty(value: str) -> int:
    if not value:
        return 1
    key = _key(value)
    if key in DIFFICULTY_WORDS:
        return DIFFICULTY_WORDS[key]
    try:
        d = int(float(key))
    except ValueError:
        raise ValueError(f"qiyinlik noto'g'ri: {value}") from None
    if d not in (1, 2, 3):
        raise ValueError(f"qiyinlik 1, 2 yoki 3 bo'lishi kerak: {value}")
    return d


async def _get_period(session: AsyncSession, name: str, cache: dict) -> Period | None:
    if not name:
        return None
    if name not in cache:
        period = await session.scalar(select(Period).where(Period.name == name))
        if period is None:
            period = Period(name=name, sort_order=len(cache) + 1)
            session.add(period)
            await session.flush()
        cache[name] = period
    return cache[name]


async def _get_topic(
    session: AsyncSession, name: str, period: Period | None, cache: dict
) -> Topic | None:
    if not name:
        return None
    key = (name, period.id if period else None)
    if key not in cache:
        q = select(Topic).where(Topic.name == name)
        if period:
            q = q.where(Topic.period_id == period.id)
        topic = await session.scalar(q)
        if topic is None:
            topic = Topic(name=name, period_id=period.id if period else None,
                          sort_order=len(cache) + 1)
            session.add(topic)
            await session.flush()
        cache[key] = topic
    return cache[key]


async def import_rows(session: AsyncSession, rows: list[dict[str, str]]) -> ImportReport:
    report = ImportReport()
    existing = set(await session.scalars(select(Question.text)))
    periods: dict = {}
    topics: dict = {}

    for line_no, row in enumerate(rows, start=2):  # 1-qator — sarlavha
        try:
            missing = [f for f in REQUIRED if not row.get(f)]
            if missing:
                raise ValueError("bo'sh maydon: " + ", ".join(missing))
            correct = row["correct"].strip().lower()
            if correct not in OPTIONS:
                raise ValueError(f"to'g'ri javob A/B/C/D bo'lishi kerak: {row['correct']}")
            difficulty = _difficulty(row.get("difficulty", ""))
        except ValueError as e:
            report.errors.append(f"{line_no}-qator: {e}")
            continue

        if row["text"] in existing:
            report.skipped_duplicates += 1
            continue

        period = await _get_period(session, row.get("period", ""), periods)
        topic = await _get_topic(session, row.get("topic", ""), period, topics)
        session.add(Question(
            text=row["text"], option_a=row["a"], option_b=row["b"],
            option_c=row["c"], option_d=row["d"], correct_option=correct,
            explanation=row.get("explanation", ""), difficulty=difficulty,
            topic_id=topic.id if topic else None, period_id=period.id if period else None,
        ))
        existing.add(row["text"])
        report.added += 1

    await session.flush()
    return report


async def import_file(session: AsyncSession, filename: str, content: bytes) -> ImportReport:
    return await import_rows(session, read_rows(filename, content))
