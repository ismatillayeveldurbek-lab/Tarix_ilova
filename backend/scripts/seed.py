"""Namuna ma'lumotlarni bazaga yuklaydi: 20 ta savol va "Tarixda bugun" voqealari.

Ishga tushirish (backend/ papkasida, `alembic upgrade head` dan keyin):
    python -m scripts.seed
Qayta ishga tushirish xavfsiz — takroriy yozuvlar qo'shilmaydi.
"""
import asyncio
import csv

from sqlalchemy import select

from app.config import BASE_DIR
from app.db import SessionLocal
from app.models import ExamConfig, HistoryEvent
from app.services.importer import import_file

DATA = BASE_DIR / "data"

# Vaqtinchalik imtihon formati. Rasmiy spetsifikatsiya chiqqach, shu yerda yoki
# admin panelda o'zgartiriladi — kodga tegish shart emas.
DEFAULT_EXAM = dict(
    name="Sinov imtihoni (namuna format)",
    duration_minutes=60,
    rules=[
        {"difficulty": 1, "count": 8, "points": 2.0},
        {"difficulty": 2, "count": 8, "points": 3.0},
        {"difficulty": 3, "count": 4, "points": 4.0},
    ],
    scoring={"max_score": 56},
    grades=[
        {"min_percent": 85, "grade": "A+"}, {"min_percent": 75, "grade": "A"},
        {"min_percent": 65, "grade": "B+"}, {"min_percent": 55, "grade": "B"},
        {"min_percent": 50, "grade": "C+"}, {"min_percent": 45, "grade": "C"},
    ],
)


async def seed() -> None:
    async with SessionLocal() as session:
        path = DATA / "sample_questions.csv"
        report = await import_file(session, path.name, path.read_bytes())
        print(f"Savollar: +{report.added}, takroriy {report.skipped_duplicates}, xato {len(report.errors)}")
        for err in report.errors:
            print("  ", err)

        existing = {(e.month, e.day, e.title) for e in await session.scalars(select(HistoryEvent))}
        added = 0
        with open(DATA / "history_events.csv", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                key = (int(row["oy"]), int(row["kun"]), row["sarlavha"])
                if key in existing:
                    continue
                session.add(HistoryEvent(
                    month=key[0], day=key[1], year=int(row["yil"]) if row["yil"] else None,
                    title=row["sarlavha"], text=row["matn"],
                ))
                added += 1
        print(f"'Tarixda bugun' voqealari: +{added}")

        if not await session.scalar(select(ExamConfig).limit(1)):
            session.add(ExamConfig(**DEFAULT_EXAM))
            print("Imtihon formati (namuna) qo'shildi")

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
