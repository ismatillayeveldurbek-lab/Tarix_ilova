"""O'yin sessiyalari. Hamma hisob (to'g'rilik, ochko, XP, soat) serverda."""
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, utcnow


class GameSession(Base):
    __tablename__ = "game_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    game: Mapped[str] = mapped_column(String(32), index=True)          # "oldin"
    round_no: Mapped[int] = mapped_column(Integer, default=1)          # bugungi nechanchi raund
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Server soati: budget — jami vaqt; used — sarflangan; running bo'lsa resumed_at dan beri ham sanaladi
    budget_ms: Mapped[int] = mapped_column(Integer, default=60_000)
    used_ms: Mapped[int] = mapped_column(Integer, default=0)
    running: Mapped[bool] = mapped_column(Boolean, default=True)
    resumed_at: Mapped[datetime | None] = mapped_column(DateTime)

    # {"pairs": [{"a": id, "b": id, "pick": None|"a"|"b", "ok": None|bool, "points": 0}], "idx": 0,
    #  "score": 0, "combo": 0, "best_combo": 0}
    state: Mapped[dict] = mapped_column(JSON, default=dict)
    xp: Mapped[int] = mapped_column(Integer, default=0)
