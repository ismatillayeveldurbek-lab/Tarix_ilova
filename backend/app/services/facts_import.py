"""Faktlarni CSV’dan bazaga import qilish (ID bo‘yicha yangilash).

* Yangi fakt qo‘shiladi, mavjudi yangilanadi.
* `hidden_admin` (admin qo‘lda yashirgani) import paytida o‘zgarmaydi.
* CSV’da endi yo‘q faktlar o‘chirilmaydi (foydalanuvchi progressi saqlanadi), balki yashiriladi.
"""
import csv
import io
from collections import Counter
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Book, Fact
from app.services.facts_validation import book_from_id, check_row

REQUIRED_COLUMNS = ("id", "tur", "nom", "matn", "kitob_id", "bet", "ishonch")
FACT_FIELDS = (
    "tur", "nom", "matn", "sana_matn", "yil_boshi", "yil_oxiri", "asr", "davr", "hudud", "sinf",
    "paragraf", "mavzu_nomi", "bet", "iqtibos", "shaxs_faoliyati", "shaxs_ishoralar", "urush_tomonlari",
    "golib", "natija", "joy_turi", "joy_hozirgi", "asar_muallifi", "ishonch", "izoh",
)


@dataclass
class FactImportReport:
    total: int = 0
    added: int = 0
    updated: int = 0
    unchanged: int = 0
    hidden: int = 0
    missing_in_csv: int = 0
    flags: Counter = field(default_factory=Counter)
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {**self.__dict__, "flags": dict(self.flags.most_common())}


def read_csv(content: bytes) -> list[dict[str, str]]:
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
    if missing:
        raise ValueError("CSV’da ustunlar yo‘q: " + ", ".join(missing))
    return list(reader)


async def import_facts(session: AsyncSession, rows: list[dict[str, str]], dry_run: bool = False) -> FactImportReport:
    report = FactImportReport(total=len(rows))
    books = {b.id: b for b in await session.scalars(select(Book))}
    existing = {f.id: f for f in await session.scalars(select(Fact))}
    seen: set[str] = set()

    for line_no, row in enumerate(rows, start=2):
        checked = check_row(row)
        d = checked.data
        if not d["id"]:
            report.errors.append(f"{line_no}-qator: id bo‘sh")
            continue
        if d["id"] in seen:
            report.errors.append(f"{line_no}-qator: takroriy id {d['id']}")
            continue
        seen.add(d["id"])
        report.flags.update(checked.flags)
        report.hidden += checked.hidden

        book = books.get(d["kitob_id"])
        if book is None:
            parsed = book_from_id(d["kitob_id"])
            if parsed is None:
                report.errors.append(f"{line_no}-qator: noma’lum kitob_id {d['kitob_id']}")
                continue
            book = Book(id=d["kitob_id"], sinf=parsed[0], fan=parsed[1])
            books[book.id] = book
            if not dry_run:
                session.add(book)

        values = {f: d[f] for f in FACT_FIELDS}
        values.update(book_id=book.id, flags=checked.flags, hidden_import=checked.hidden)
        fact = existing.get(d["id"])
        if fact is None:
            report.added += 1
            if not dry_run:
                session.add(Fact(id=d["id"], **values))
        else:
            changed = any(getattr(fact, k) != v for k, v in values.items())
            if changed:
                report.updated += 1
                if not dry_run:
                    for k, v in values.items():
                        setattr(fact, k, v)
            else:
                report.unchanged += 1

    for fid, fact in existing.items():
        if fid not in seen and not fact.hidden_import:
            report.missing_in_csv += 1
            if not dry_run:
                fact.hidden_import = True
                fact.flags = [*fact.flags, "csvda_yoq"]
    if not dry_run:
        await session.flush()
    return report
