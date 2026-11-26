"""Loyiha sozlamalari.

Barcha maxfiy va o‘zgaruvchan qiymatlar (bot tokeni, baza manzili...)
`.env` faylidan o‘qiladi. Kodga hech qachon token yozilmaydi.
"""
import re
from functools import cached_property
from pathlib import Path
from zoneinfo import ZoneInfo

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import field_validator, model_validator
from sqlalchemy.engine import make_url
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/ papkasi


def clean_db_url(v: str) -> str:
    """Nusxalashda tushib qoladigan ortiqcha narsalarni olib tashlaydi:
    psql 'postgresql://...'  |  "postgresql://..."  |  DATABASE_URL=postgresql://...
    """
    v = (v or "").strip()
    m = re.search(r"(postgres(?:ql)?(?:\+asyncpg)?://[^\s'\"]+)", v)
    if m:
        return m.group(1)
    return v.strip("'\" ")


def normalize_db_url(v: str) -> str:
    """postgres://u:p@host/db?sslmode=require&channel_binding=require
    -> postgresql+asyncpg://u:p@host/db?ssl=require

    asyncpg `sslmode` va `channel_binding` parametrlarini tushunmaydi. Neon'ning
    "-pooler" manzilida tayyorlangan so‘rovlar keshi o‘chiriladi (PgBouncer bilan mos).
    """
    v = clean_db_url(v)
    for prefix in ("postgres://", "postgresql://"):
        if v.startswith(prefix):
            v = "postgresql+asyncpg://" + v[len(prefix):]
    if not v.startswith("postgresql+asyncpg://"):
        return v
    parts = urlsplit(v)
    query = dict(parse_qsl(parts.query))
    query.pop("channel_binding", None)
    sslmode = query.pop("sslmode", None)
    if sslmode and sslmode != "disable":
        query.setdefault("ssl", "require")
    if "-pooler" in (parts.hostname or ""):
        query.setdefault("prepared_statement_cache_size", "0")
    return urlunsplit(parts._replace(query=urlencode(query)))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore",
        hide_input_in_errors=True,  # xato xabarida token/parol ko‘rinmasin
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
    render_external_url: str = ""  # Render o‘zi qo‘yadi (https://nom.onrender.com)
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
        """Neon/Render/Railway "postgres://...?sslmode=require" beradi — asyncpg'ga moslaymiz."""
        url = normalize_db_url(v)
        try:
            make_url(url)
        except Exception:
            # Qiymatning o‘zi logga chiqmaydi: unda parol bor
            raise ValueError(
                "DATABASE_URL noto‘g‘ri. U postgresql://... bilan boshlanishi kerak "
                "(Neon → Connect oynasidagi manzil, psql so‘zisiz va qo‘shtirnoqsiz)") from None
        return url

    @model_validator(mode="after")
    def _render_url(self) -> "Settings":
        """Render o‘z domenini RENDER_EXTERNAL_URL da beradi: WEBAPP_URL bo‘sh bo‘lsa shuni olamiz."""
        if not self.webapp_url and self.render_external_url:
            self.webapp_url = self.render_external_url
        return self

    @cached_property
    def admin_id_list(self) -> set[int]:
        return {int(x) for x in self.admin_ids.replace(" ", "").split(",") if x}

    @cached_property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)


settings = Settings()
