"""Faktlar bazasidan test savollarini tuzish va bazaga yozish.

Ishga tushirish (backend/ papkasida):
    python -m scripts.generate_questions

Qayta ishga tushirish xavfsiz: savollar fakt bo'yicha yangilanadi, admin tahrirlaganlarga
tegilmaydi. Faktlar importidan keyin avtomatik ham ishlaydi (Dockerfile).
"""
import asyncio

from app.db import SessionLocal
from app.services.question_gen import sync_questions

KIND_NAMES = {"qachon": "sana (qachon?)", "kim": "shaxs (kim men?)", "atama": "atama", "joy": "joy",
              "muallif": "asar muallifi", "asar": "asar / yodgorlik", "golib": "urush g‘olibi"}


async def main() -> None:
    async with SessionLocal() as session:
        r = await sync_questions(session)
        await session.commit()
    print(f"SAVOLLAR: {r.total} ta tuzildi")
    print(f"  Qo‘shildi: {r.added} · yangilandi: {r.updated} · o‘zgarmadi: {r.unchanged}")
    print(f"  Admin tahrirlagan (tegilmadi): {r.locked} · o‘chirildi: {r.deactivated}")
    for kind, n in sorted(r.by_kind.items(), key=lambda x: -x[1]):
        print(f"    {n:5}  {KIND_NAMES.get(kind, kind)}")


if __name__ == "__main__":
    asyncio.run(main())
