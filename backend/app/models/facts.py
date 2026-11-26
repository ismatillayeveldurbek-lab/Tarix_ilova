"""Faktlar bazasi: darsliklar, faktlar, foydalanuvchi faktining holati, kunlik hisob.

Hamma narsa (kartochka, test, o‘yin) shu faktlardan tuziladi. Har fakt darslik,
paragraf va betga bog‘langan — foydalanuvchiga doim manba ko‘rsatiladi.
"""
from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, utcnow

FACT_TYPES = ("sana", "shaxs", "atama", "joy", "urush", "asar")

# Foydalanuvchi faktining holatlari (SRS)
STATE_NEW = "yangi"
STATE_LEARNING = "organilmoqda"
STATE_DUE = "takrorlash_kerak"
STATE_MASTERED = "ozlashtirildi"


class Book(Base):
    """Darslik. id — CSV’dagi kitob_id (masalan, K08J: 8-sinf, Jahon tarixi)."""

    __tablename__ = "books"

    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    sinf: Mapped[int] = mapped_column(Integer)
    fan: Mapped[str] = mapped_column(String(64))  # "Jahon tarixi" | "O‘zbekiston tarixi"
    nashr_yili: Mapped[int | None] = mapped_column(Integer)

    @property
    def title(self) -> str:
        return f"{self.sinf}-sinf {self.fan}"


class Fact(Base):
    __tablename__ = "facts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)  # CSV id, masalan K06J-0001
    tur: Mapped[str] = mapped_column(String(16), index=True)
    nom: Mapped[str] = mapped_column(String(500))
    matn: Mapped[str] = mapped_column(Text)
    sana_matn: Mapped[str] = mapped_column(String(255), default="")
    yil_boshi: Mapped[int | None] = mapped_column(Integer, index=True)  # mil. avv. — manfiy
    yil_oxiri: Mapped[int | None] = mapped_column(Integer)
    asr: Mapped[str] = mapped_column(String(64), default="")
    davr: Mapped[str] = mapped_column(String(32), index=True)
    hudud: Mapped[str] = mapped_column(String(64), index=True)
    sinf: Mapped[int] = mapped_column(Integer, index=True)
    book_id: Mapped[str] = mapped_column(ForeignKey("books.id"), index=True)
    paragraf: Mapped[str] = mapped_column(String(32), default="")
    mavzu_nomi: Mapped[str] = mapped_column(String(500), default="")
    bet: Mapped[str] = mapped_column(String(32), default="")
    iqtibos: Mapped[str] = mapped_column(Text, default="")

    shaxs_faoliyati: Mapped[str] = mapped_column(String(64), default="")
    shaxs_ishoralar: Mapped[list] = mapped_column(JSON, default=list)
    urush_tomonlari: Mapped[list] = mapped_column(JSON, default=list)
    golib: Mapped[str] = mapped_column(String(255), default="")
    natija: Mapped[str] = mapped_column(Text, default="")
    joy_turi: Mapped[str] = mapped_column(String(64), default="")
    joy_hozirgi: Mapped[str] = mapped_column(String(255), default="")
    asar_muallifi: Mapped[str] = mapped_column(String(255), default="")

    ishonch: Mapped[str] = mapped_column(String(16), default="yuqori")
    izoh: Mapped[str] = mapped_column(Text, default="")  # metodist izohi — foydalanuvchiga ko‘rsatilmaydi

    # Tekshiruv natijasi (import paytida): ["yil_yoq", "atama_ozini_tushuntiradi", ...]
    flags: Mapped[list] = mapped_column(JSON, default=list)
    hidden_import: Mapped[bool] = mapped_column(Boolean, default=False)  # ishonch=past yoki jiddiy xato
    hidden_admin: Mapped[bool] = mapped_column(Boolean, default=False)   # admin qo‘lda yashirgan
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    book: Mapped[Book] = relationship(lazy="joined")

    @property
    def visible(self) -> bool:
        return not (self.hidden_import or self.hidden_admin)

    @property
    def source(self) -> str:
        """Masalan: "8-sinf Jahon tarixi, 10-§, 63-bet"."""
        parts = [self.book.title if self.book else self.book_id]
        if self.paragraf:
            parts.append(self.paragraf)
        if self.bet:
            parts.append(f"{self.bet}-bet")
        return ", ".join(parts)


class UserFactState(Base):
    """Foydalanuvchining bitta fakt bo‘yicha holati (oraliqli takrorlash)."""

    __tablename__ = "user_fact_state"
    __table_args__ = (UniqueConstraint("user_id", "fact_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    fact_id: Mapped[str] = mapped_column(ForeignKey("facts.id"), index=True)
    holat: Mapped[str] = mapped_column(String(20), default=STATE_NEW)
    step: Mapped[int] = mapped_column(Integer, default=0)            # nechanchi oraliqda turibdi
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    wrong_count: Mapped[int] = mapped_column(Integer, default=0)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime)


class DailyStat(Base):
    """Kunlik hisob (Toshkent sanasi bo‘yicha): XP, ko‘rilgan kartalar, o‘yinlar."""

    __tablename__ = "daily_stats"
    __table_args__ = (UniqueConstraint("user_id", "day"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    day: Mapped[date] = mapped_column(Date, index=True)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    cards_reviewed: Mapped[int] = mapped_column(Integer, default=0)
    new_cards: Mapped[int] = mapped_column(Integer, default=0)  # bugun boshlangan yangi kartalar (limit uchun)
    actions: Mapped[int] = mapped_column(Integer, default=0)    # bugungi faollik: test + karta + o'yin javoblari
    games_played: Mapped[int] = mapped_column(Integer, default=0)
    game_xp: Mapped[dict] = mapped_column(JSON, default=dict)  # {"oldin": 40} — o‘yin bo‘yicha XP (limit uchun)
