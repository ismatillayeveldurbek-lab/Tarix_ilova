from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class HistoryEvent(Base):
    """'Tarixda bugun' voqealari."""

    __tablename__ = "history_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    month: Mapped[int] = mapped_column(Integer, index=True)
    day: Mapped[int] = mapped_column(Integer, index=True)
    year: Mapped[int | None] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(255))
    text: Mapped[str] = mapped_column(Text, default="")
    last_posted_year: Mapped[int | None] = mapped_column(Integer)
