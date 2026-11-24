"""Loyiha sozlamalari.

Barcha maxfiy va o'zgaruvchan qiymatlar (bot tokeni, baza manzili...)
`.env` faylidan o'qiladi. Kodga hech qachon token yozilmaydi.
"""
from functools import cached_property
from pathlib import Path
from zoneinfo import ZoneInfo

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/ papkasi


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    bot_token: str = ""
    database_url: str = f"sqlite+aiosqlite:///{BASE_DIR / 'tarix.db'}"
    admin_ids: str = ""          # "111,222" ko'rinishida
    channel_id: str = ""         # "@kanal" yoki "-100..."
    timezone: str = "Asia/Tashkent"
    reminder_time: str = "19:00"
    daily_question_count: int = 10
    quiz_length: int = 10
    webapp_url: str = ""         # Mini App manzili (5-bosqichda)

    @cached_property
    def admin_id_list(self) -> set[int]:
        return {int(x) for x in self.admin_ids.replace(" ", "").split(",") if x}

    @cached_property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)


settings = Settings()
