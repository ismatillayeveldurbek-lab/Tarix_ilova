""""Tarixda bugun" — bugungi sanaga oid voqealar."""
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import local_today
from app.models import HistoryEvent
from app.services.translit import tr


async def events_for(session: AsyncSession, day: date | None = None) -> list[HistoryEvent]:
    day = day or local_today()
    return list(await session.scalars(
        select(HistoryEvent).where(HistoryEvent.month == day.month, HistoryEvent.day == day.day)
        .order_by(HistoryEvent.year)
    ))


MONTHS = ["yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul",
          "avgust", "sentabr", "oktabr", "noyabr", "dekabr"]


def format_post(events: list[HistoryEvent], day: date, alphabet: str = "latn") -> str:
    import html
    lines = [f"📅 <b>Tarixda bugun — {day.day}-{MONTHS[day.month - 1]}</b>", ""]
    for e in events:
        year = f"{e.year}-yil. " if e.year else ""
        lines.append(f"🔹 <b>{html.escape(year + e.title, quote=False)}</b>")
        if e.text:
            lines.append(html.escape(e.text, quote=False))
        lines.append("")
    lines.append("#tarixda_bugun")
    return tr("\n".join(lines), alphabet)
