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

    reminder_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    reminder_time: Mapped[time] = mapped_column(Time, default=time(19, 0))

    streak_current: Mapped[int] = mapped_column(Integer, default=0)
    streak_best: Mapped[int] = mapped_column(Integer, default=0)
    last_active_date: Mapped[date | None] = mapped_column(Date)

    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)  # botni bloklagan
    last_reminder_date: Mapped[date | None] = mapped_column(Date)  # eslatma ikki marta ketmasin

    # Referal: shaxsiy taklif kodi va kim taklif qilgani
    ref_code: Mapped[str | None] = mapped_column(String(16), unique=True, index=True)
    referred_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    # --- Kelajak uchun (hozir ishlatilmaydi) ---
    premium_until: Mapped[datetime | None] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Referral(Base):
    """Taklif: kim kimni taklif qildi. Do‘st yetarli savol yechganda "faol" bo‘ladi va bonus beriladi."""

    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(primary_key=True)
    inviter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    invited_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime)


class XpBonus(Base):
    """Javobdan tashqari XP (masalan, taklif bonusi). Haftalik reytingga qo‘shiladi."""

    __tablename__ = "xp_bonuses"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    amount: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
