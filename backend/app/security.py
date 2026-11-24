"""Xavfsizlik: Telegram Mini App ma'lumotini tekshirish va admin panel uchun token.

1) Mini App ochilganda Telegram `initData` satrini beradi. U bot tokeni bilan imzolangan,
   shuning uchun uni soxtalashtirib bo'lmaydi. Server imzoni tekshiradi.
2) Admin panelni brauzerda ochish uchun bot /panel buyrug'ida vaqtinchalik token beradi.
"""
import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from app.config import settings

ADMIN_TOKEN_TTL = 12 * 3600  # 12 soat


def validate_init_data(init_data: str, max_age: int = 24 * 3600) -> dict | None:
    """To'g'ri bo'lsa Telegram foydalanuvchisi (dict) qaytadi, aks holda None."""
    try:
        pairs = dict(parse_qsl(init_data, strict_parsing=True))
    except ValueError:
        return None
    received_hash = pairs.pop("hash", None)
    if not received_hash or not settings.bot_token:
        return None
    check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret = hmac.new(b"WebAppData", settings.bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received_hash):
        return None
    if time.time() - int(pairs.get("auth_date", 0)) > max_age:
        return None
    try:
        return json.loads(pairs["user"])
    except (KeyError, ValueError):
        return None


def _admin_secret() -> bytes:
    return hashlib.sha256(("admin-panel:" + settings.bot_token).encode()).digest()


def make_admin_token(telegram_id: int, ttl: int = ADMIN_TOKEN_TTL) -> str:
    payload = f"{telegram_id}.{int(time.time()) + ttl}"
    sig = hmac.new(_admin_secret(), payload.encode(), hashlib.sha256).hexdigest()[:40]
    return f"{payload}.{sig}"


def verify_admin_token(token: str) -> int | None:
    try:
        tid, exp, sig = token.split(".")
        payload = f"{tid}.{exp}"
        expected = hmac.new(_admin_secret(), payload.encode(), hashlib.sha256).hexdigest()[:40]
        if hmac.compare_digest(expected, sig) and int(exp) > time.time():
            return int(tid)
    except ValueError:
        pass
    return None
