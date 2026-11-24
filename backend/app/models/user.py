from datetime import date, datetime, time

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, utcnow


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    username: Mapped[str | None] = mapped_column(String(64))

    alphabet: Mapped[str] = mapped_column(String(4), default="latn")  # 'latn' | 'cyrl'
    alphabet_chosen: Mapped[bool] = mapped_column(Boolean, default=False)

    reminder_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    reminder_time: Mapped[time] = mapped_column(Time, default=time(19, 0))

    streak_current: Mapped[int] = mapped_column(Integer, default=0)
    streak_best: Mapped[int] = mapped_column(Integer, default=0)
    last_active_date: Mapped[date | None] = mapped_column(Date)

    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)  # botni bloklagan

    # --- Kelajak uchun (hozir ishlatilmaydi) ---
    premium_until: Mapped[datetime | None] = mapped_column(DateTime)
    referred_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
