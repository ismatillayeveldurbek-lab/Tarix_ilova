"""Savollarni Excel (.xlsx) yoki CSV fayldan import qilish.

Fayl birinchi qatorida ustun nomlari bo‘lishi kerak:
    savol | a | b | c | d | togri | izoh | mavzu | davr | qiyinlik | rasm | manba | vaqt_savoli

- togri: A, B, C yoki D
- qiyinlik: 1/2/3 yoki oson/o‘rta/qiyin (bo‘sh bo‘lsa — 1)
- mavzu va davr bazada bo‘lmasa, avtomatik yaratiladi
- rasm (ixtiyoriy): rasmning https:// havolasi
- manba (ixtiyoriy): "7-sinf Jahon tarixi, 5-§, 40-bet" — izoh oxiriga "Manba: ..." bo‘lib qo‘shiladi
- vaqt_savoli (ixtiyoriy): ha/yo‘q — sana so‘raladigan savolda javobdan oldin davr va mavzu ko‘rsatilmaydi
- matni bir xil savol ikkinchi marta qo‘shilmaydi
"""
import csv
import io
from dataclasses import dataclass, field

from openpyxl import load_workbook
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OPTIONS, Period, Question, Topic
from app.services.facts_validation import clean_text
from app.services.media import is_valid_image_url

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
    "rasm": "image", "image": "image", "rasm url": "image", "rasm havolasi": "image",
    "manba": "source", "source": "source",
    "vaqt_savoli": "asks_time", "vaqt savoli": "asks_time",
}
YES = {"ha", "yes", "1", "true", "+"}
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


def read_table(filename: str, content: bytes) -> list[list]:
    """Excel yoki CSV faylni qatorlar ro‘yxatiga aylantiradi."""
    name = filename.lower()
    if name.endswith(".xlsx"):
        try:
            wb = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        except Exception:
            raise ValueError("Excel fayl o‘qilmadi (fayl buzilgan yoki .xlsx emas)") from None
        return [list(r) for r in wb.active.iter_rows(values_only=True)]
    if name.endswith(".csv"):
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = content.decode("cp1251")  # Excel ba’zan shu kodlashda saqlaydi
        try:
            dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        return list(csv.reader(io.StringIO(text), dialect))
    raise ValueError("Faqat .xlsx yoki .csv fayl qabul qilinadi")


def _map_rows(raw: list[list], aliases: dict[str, str], required: tuple[str, ...]) -> list[dict[str, str]]:
    if not raw:
        return []
    headers = [aliases.get(_key(h)) for h in raw[0]]
    missing = [r for r in required if r not in headers]
    if missing:
        raise ValueError("Ustunlar topilmadi: " + ", ".join(missing))
    rows = []
    header_keys = [_key(h) for h in raw[0]]
    for values in raw[1:]:
        if [_key(v) for v in values[:len(header_keys)]] == header_keys:
            continue  # bir nechta ChatGPT javobi bitta faylga qo'shilganda sarlavha takrorlanadi
        row = {h: _norm(v) for h, v in zip(headers, values) if h}
        if any(row.values()):
            rows.append(row)
    return rows


def read_rows(filename: str, content: bytes) -> list[dict[str, str]]:
    """Savollar faylini o‘qib, har bir qatorni {ichki_nom: qiymat} lug‘atiga aylantiradi."""
    return _map_rows(read_table(filename, content), HEADER_ALIASES, REQUIRED)


def _difficulty(value: str) -> int:
    if not value:
        return 1
    key = _key(value)
    if key in DIFFICULTY_WORDS:
        return DIFFICULTY_WORDS[key]
    try:
        d = int(float(key))
    except ValueError:
        raise ValueError(f"qiyinlik noto‘g‘ri: {value}") from None
    if d not in (1, 2, 3):
        raise ValueError(f"qiyinlik 1, 2 yoki 3 bo‘lishi kerak: {value}")
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


def _row_values(row: dict[str, str]) -> dict:
    """Bitta qatorni tekshiradi va Question maydonlariga aylantiradi (davr/mavzu — nomlari bilan).
    Xato bo‘lsa ValueError."""
    missing = [f for f in REQUIRED if not row.get(f)]
    if missing:
        raise ValueError("bo‘sh maydon: " + ", ".join(missing))
    correct = row["correct"].strip().lower()
    if correct not in OPTIONS:
        raise ValueError(f"to‘g‘ri javob A/B/C/D bo‘lishi kerak: {row['correct']}")
    difficulty = _difficulty(row.get("difficulty", ""))
    image = row.get("image", "")
    if image and not is_valid_image_url(image):
        raise ValueError(f"rasm havolasi http(s):// bilan boshlanishi kerak: {image}")
    explanation = clean_text(row.get("explanation", ""))
    source = clean_text(row.get("source", ""))
    if source and "Manba:" not in explanation:
        explanation = f"{explanation}\n\nManba: {source}".strip()
    return {
        "text": clean_text(row["text"]), "option_a": clean_text(row["a"]), "option_b": clean_text(row["b"]),
        "option_c": clean_text(row["c"]), "option_d": clean_text(row["d"]), "correct_option": correct,
        "explanation": explanation, "difficulty": difficulty, "image_url": image or None,
        "asks_time": _key(row.get("asks_time", "")) in YES,
        "_period": clean_text(row.get("period", "")), "_topic": clean_text(row.get("topic", "")),
    }


async def import_rows(session: AsyncSession, rows: list[dict[str, str]]) -> ImportReport:
    report = ImportReport()
    existing = set(await session.scalars(select(Question.text)))
    periods: dict = {}
    topics: dict = {}

    for line_no, row in enumerate(rows, start=2):  # 1-qator — sarlavha
        try:
            values = _row_values(row)
        except ValueError as e:
            report.errors.append(f"{line_no}-qator: {e}")
            continue
        if values["text"] in existing:
            report.skipped_duplicates += 1
            continue
        period = await _get_period(session, values.pop("_period"), periods)
        topic = await _get_topic(session, values.pop("_topic"), period, topics)
        session.add(Question(**values, topic_id=topic.id if topic else None, period_id=period.id if period else None))
        existing.add(values["text"])
        report.added += 1

    await session.flush()
    return report


@dataclass
class SyncFilesReport:
    files: int = 0
    added: int = 0
    updated: int = 0
    unchanged: int = 0
    locked: int = 0
    deactivated: int = 0
    errors: list[str] = field(default_factory=list)


async def sync_test_files(session: AsyncSession, folder) -> SyncFilesReport:
    """data/testlar/*.csv — mavzu testlari (docs/promptlar/07-mavzu-testlari.md).
    Har savol "test:<fayl>:<qator>" kaliti bilan saqlanadi: fayl tuzatilib qayta yuklansa savol
    YANGILANADI (ikki nusxa bo‘lmaydi), fayldan olib tashlangan savol o‘chiriladi.
    Admin tahrirlagan (locked) savolga tegilmaydi."""
    from pathlib import Path

    rep = SyncFilesReport()
    files = sorted(Path(folder).glob("*.csv")) + sorted(Path(folder).glob("*.xlsx"))
    existing = {q.gen_key: q for q in await session.scalars(select(Question).where(Question.gen_key.like("test:%")))}
    periods: dict = {}
    topics: dict = {}
    seen: set[str] = set()
    ok_files: set[str] = set()
    for path in files:
        rep.files += 1
        try:
            rows = read_rows(path.name, path.read_bytes())
        except (ValueError, UnicodeDecodeError) as e:
            rep.errors.append(f"{path.name}: {e}")
            continue
        ok_files.add(path.stem)
        for line_no, row in enumerate(rows, start=2):
            key = f"test:{path.stem}:{line_no}"
            try:
                values = _row_values(row)
            except ValueError as e:
                rep.errors.append(f"{path.name}, {line_no}-qator: {e}")
                continue
            seen.add(key)
            period = await _get_period(session, values.pop("_period"), periods)
            topic = await _get_topic(session, values.pop("_topic"), period, topics)
            values.update(topic_id=topic.id if topic else None, period_id=period.id if period else None, is_active=True)
            q = existing.get(key)
            if q is None:
                session.add(Question(gen_key=key, **values))
                rep.added += 1
            elif q.locked:
                rep.locked += 1
            elif any(getattr(q, k) != v for k, v in values.items()):
                for k, v in values.items():
                    setattr(q, k, v)
                rep.updated += 1
            else:
                rep.unchanged += 1
    for key, q in existing.items():
        stem = key.split(":")[1]
        # o'qib bo'lmagan fayl savollariga tegilmaydi (xato tuzatilguncha eskisi ishlab tursin)
        if key not in seen and (stem in ok_files or stem not in {p.stem for p in files}) and not q.locked and q.is_active:
            q.is_active = False
            rep.deactivated += 1
    await session.flush()
    return rep


async def import_file(session: AsyncSession, filename: str, content: bytes) -> ImportReport:
    return await import_rows(session, read_rows(filename, content))


# ---------- "Tarixda bugun" voqealari ----------
# Ustunlar: oy | kun | yil | sarlavha | matn
HISTORY_ALIASES = {
    "oy": "month", "month": "month", "kun": "day", "day": "day", "yil": "year", "year": "year",
    "sarlavha": "title", "title": "title", "voqea": "title",
    "matn": "text", "text": "text", "izoh": "text",
}


async def import_history_file(session: AsyncSession, filename: str, content: bytes) -> ImportReport:
    from app.models import HistoryEvent

    rows = _map_rows(read_table(filename, content), HISTORY_ALIASES, ("month", "day", "title"))
    report = ImportReport()
    existing = {(e.month, e.day, e.title) for e in await session.scalars(select(HistoryEvent))}
    for line_no, row in enumerate(rows, start=2):
        try:
            month, day = int(float(row["month"])), int(float(row["day"]))
            year = int(float(row["year"])) if row.get("year") else None
            if not (1 <= month <= 12 and 1 <= day <= 31):
                raise ValueError("oy 1–12, kun 1–31 bo‘lishi kerak")
            if not row.get("title"):
                raise ValueError("sarlavha bo‘sh")
        except (ValueError, KeyError) as e:
            report.errors.append(f"{line_no}-qator: {e}")
            continue
        key = (month, day, row["title"])
        if key in existing:
            report.skipped_duplicates += 1
            continue
        session.add(HistoryEvent(month=month, day=day, year=year, title=clean_text(row["title"]),
                                 text=clean_text(row.get("text", ""))))
        existing.add(key)
        report.added += 1
    await session.flush()
    return report
