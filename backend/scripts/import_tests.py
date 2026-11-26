"""Mavzu testlarini data/testlar/ papkasidan yuklash (ChatGPT bilan tayyorlangan CSV/Excel).

Ishga tushirish (backend/ papkasida):
    python -m scripts.import_tests

Qayta ishga tushirish xavfsiz: tuzatilgan fayl savollarni yangilaydi, ikki nusxa bo‘lmaydi.
Server har ishga tushganda avtomatik chaqiriladi (Dockerfile).
"""
import asyncio

from app.config import BASE_DIR
from app.db import SessionLocal
from app.services.importer import sync_test_files

FOLDER = BASE_DIR.parent / "data" / "testlar"


async def main() -> None:
    async with SessionLocal() as session:
        r = await sync_test_files(session, FOLDER)
        await session.commit()
    print(f"MAVZU TESTLARI: {r.files} ta fayl")
    print(f"  Qo‘shildi: {r.added} · yangilandi: {r.updated} · o‘zgarmadi: {r.unchanged}")
    print(f"  Admin tahrirlagan (tegilmadi): {r.locked} · o‘chirildi: {r.deactivated}")
    for e in r.errors[:30]:
        print("  XATO:", e)


if __name__ == "__main__":
    asyncio.run(main())
