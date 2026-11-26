"""Loyiha sozlamalari.

Barcha maxfiy va o‘zgaruvchan qiymatlar (bot tokeni, baza manzili...)
`.env` faylidan o‘qiladi. Kodga hech qachon token yozilmaydi.
"""
from functools import cached_property
from pathlib import Path
from zoneinfo import ZoneInfo

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/ papkasi


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    bot_token: str = ""
    database_url: str = f"sqlite+aiosqlite:///{BASE_DIR / 'tarix.db'}"
    admin_ids: str = ""          # "111,222" ko‘rinishida
    channel_id: str = ""         # "@kanal" yoki "-100..."
    timezone: str = "Asia/Tashkent"
    reminder_time: str = "19:00"
    daily_question_count: int = 10
    quiz_length: int = 10
    history_post_time: str = "09:00"  # "Tarixda bugun" posti vaqti
    webapp_url: str = ""         # Mini App manzili (https://...), masalan Railway domeni
    port: int = 8000
    bot_username: str = ""        # havolalar uchun; bo‘sh bo‘lsa bot o‘zi aniqlaydi

    # Referal tizimi
    referral_min_answers: int = 5   # do‘st shuncha savol yechgach taklif "faol" bo‘ladi
    referral_xp_inviter: int = 50   # taklif qilganga bonus
    referral_xp_invited: int = 20   # taklif qilinganga bonus
    # FAQAT kompyuterda sinash uchun: Telegram’siz brauzerda shu ID bilan kirish.
    # Serverda HECH QACHON yoqmang!
    dev_telegram_id: int = 0

    @field_validator("database_url")
    @classmethod
    def _async_driver(cls, v: str) -> str:
        """Railway/Render "postgres://..." beradi — asinxron drayverni qo‘shamiz."""
        for prefix in ("postgres://", "postgresql://"):
            if v.startswith(prefix):
                return "postgresql+asyncpg://" + v[len(prefix):]
        return v

    @cached_property
    def admin_id_list(self) -> set[int]:
        return {int(x) for x in self.admin_ids.replace(" ", "").split(",") if x}

    @cached_property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)


settings = Settings()
