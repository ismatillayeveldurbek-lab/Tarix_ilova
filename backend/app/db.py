"""Ma’lumotlar bazasiga ulanish."""
from datetime import UTC, date, datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    """Barcha jadvallar shu klassdan meros oladi."""


def utcnow() -> datetime:
    """Hozirgi vaqt (UTC). Bazada vaqtlar UTC’da saqlanadi."""
    return datetime.now(UTC).replace(tzinfo=None)


def local_today() -> date:
    """Toshkent vaqti bo‘yicha bugungi sana (streak uchun)."""
    return datetime.now(settings.tz).date()
