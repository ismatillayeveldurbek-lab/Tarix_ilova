"""Faktlar bazasini CSV’dan import qilish.

Ishga tushirish (backend/ papkasida):
    python -m scripts.import_facts                  # ../data/baza.csv
    python -m scripts.import_facts yo‘l/fayl.csv
    python -m scripts.import_facts --dry-run        # faqat tekshiradi, bazaga yozmaydi

Qayta ishga tushirish xavfsiz: faktlar ID bo‘yicha yangilanadi.
"""
import asyncio
import sys
from pathlib import Path

from app.config import BASE_DIR
from app.db import SessionLocal
from app.services.facts_import import import_facts, read_csv

DEFAULT_CSV = BASE_DIR.parent / "data" / "baza.csv"

FLAG_NAMES = {
    "ishonch_past": "ishonch past (yashirildi)",
    "manba_yoq": "manba yo‘q (yashirildi)",
    "tur_nomalum": "turi noma’lum (yashirildi)",
    "matn_yoq": "matn yo‘q (yashirildi)",
    "yil_yoq": "sana, lekin aniq yil yo‘q (yil o‘yinlarida yo‘q)",
    "yil_xato": "yil son emas",
    "yil_asr_mos_emas": "yil va asr mos emas",
    "atama_ozini_tushuntiradi": "atama ta’rifida o‘zi bor (savolda yashiriladi)",
    "kontekstsiz": "kontekstsiz gap (\"Bu...\", \"U...\")",
    "ishoralar_kam": "shaxsda 3 tadan kam ishora",
}


async def main(path: Path, dry_run: bool) -> None:
    rows = read_csv(path.read_bytes())
    async with SessionLocal() as session:
        r = await import_facts(session, rows, dry_run=dry_run)
        if not dry_run:
            await session.commit()
    print(f"{'TEKSHIRUV (bazaga yozilmadi)' if dry_run else 'IMPORT'}: {path.name}")
    print(f"  Jami qatorlar: {r.total}")
    print(f"  Qo‘shildi: {r.added} · yangilandi: {r.updated} · o‘zgarmadi: {r.unchanged}")
    print(f"  Foydalanuvchidan yashirildi: {r.hidden}")
    if r.missing_in_csv:
        print(f"  CSV’da endi yo‘q (yashirildi): {r.missing_in_csv}")
    if r.flags:
        print("  Tekshiruv belgilari:")
        for flag, n in r.flags.most_common():
            print(f"    {n:5}  {FLAG_NAMES.get(flag, flag)}")
    for e in r.errors[:20]:
        print("  XATO:", e)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    asyncio.run(main(Path(args[0]) if args else DEFAULT_CSV, "--dry-run" in sys.argv))
