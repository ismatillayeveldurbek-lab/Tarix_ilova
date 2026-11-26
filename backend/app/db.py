"""Ma’lumotlar bazasiga ulanish."""
from datetime import UTC, date, datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# PostgreSQL (Neon): baza 5 daqiqa jim tursa uxlaydi va ulanishlarni uzadi. 4 daqiqadan eski ulanish
# qayta ochiladi — uzilgan ulanishga so‘rov yuborilib, xato yoki kutish bo‘lmasin.
_pg = settings.database_url.startswith("postgresql")
engine = create_async_engine(
    settings.database_url,
    **({"pool_size": 5, "max_overflow": 10, "pool_recycle": 240, "pool_timeout": 15} if _pg else {}),
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    """Barcha jadvallar shu klassdan meros oladi."""


def utcnow() -> datetime:
    """Hozirgi vaqt (UTC). Bazada vaqtlar UTC’da saqlanadi."""
    return datetime.now(UTC).replace(tzinfo=None)


def local_today() -> date:
    """Toshkent vaqti bo‘yicha bugungi sana (streak uchun)."""
    return datetime.now(settings.tz).date()
