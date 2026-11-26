"""Namuna ma’lumotlarni bazaga yuklaydi: 20 ta savol va "Tarixda bugun" voqealari.

Ishga tushirish (backend/ papkasida, `alembic upgrade head` dan keyin):
    python -m scripts.seed                 # namuna savollar + voqealar + imtihon formati
    python -m scripts.seed --faqat-format  # faqat imtihon formati (serverda shu ishlatiladi)
Qayta ishga tushirish xavfsiz — takroriy yozuvlar qo‘shilmaydi.
"""
import asyncio
import sys

from sqlalchemy import select

from app.config import BASE_DIR
from app.db import SessionLocal
from app.models import ExamConfig
from app.services.importer import import_file, import_history_file

DATA = BASE_DIR / "data"

# Vaqtinchalik imtihon formati. Rasmiy spetsifikatsiya chiqqach, shu yerda yoki
# admin panelda o‘zgartiriladi — kodga tegish shart emas.
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


async def seed(samples: bool = True) -> None:
    async with SessionLocal() as session:
        if samples:
            await load_samples(session)
        if not await session.scalar(select(ExamConfig).limit(1)):
            session.add(ExamConfig(**DEFAULT_EXAM))
            print("Imtihon formati (namuna) qo‘shildi")
        await session.commit()


async def load_samples(session) -> None:
    path = DATA / "sample_questions.csv"
    report = await import_file(session, path.name, path.read_bytes())
    print(f"Savollar: +{report.added}, takroriy {report.skipped_duplicates}, xato {len(report.errors)}")
    for err in report.errors:
        print("  ", err)

    path = DATA / "history_events.csv"
    h = await import_history_file(session, path.name, path.read_bytes())
    print(f"'Tarixda bugun' voqealari: +{h.added}")


if __name__ == "__main__":
    asyncio.run(seed(samples="--faqat-format" not in sys.argv))
