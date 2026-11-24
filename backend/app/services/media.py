"""Rasmlarni saqlash va tekshirish."""
import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Media

MAX_IMAGE_BYTES = 2 * 1024 * 1024  # 2 MB
MEDIA_PATH = re.compile(r"^/api/media/(\d+)$")

# Fayl turini kengaytmaga emas, ichidagi "imzo" baytlariga qarab aniqlaymiz (xavfsizroq)
SIGNATURES = [
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
]


def detect_image(data: bytes) -> str | None:
    for sig, mime in SIGNATURES:
        if data.startswith(sig):
            return mime
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


async def save_image(session: AsyncSession, data: bytes) -> Media:
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError("Rasm 2 MB dan katta. Uni kichikroq qilib saqlang")
    mime = detect_image(data)
    if mime is None:
        raise ValueError("Faqat PNG, JPG, WEBP yoki GIF rasm yuklash mumkin")
    media = Media(mime=mime, data=data)
    session.add(media)
    await session.flush()
    return media


def media_id(url: str | None) -> int | None:
    """"/api/media/12" -> 12 (admin yuklagan rasm bo'lsa)."""
    m = MEDIA_PATH.match(url or "")
    return int(m.group(1)) if m else None


def is_valid_image_url(url: str) -> bool:
    return bool(media_id(url)) or url.startswith("https://") or url.startswith("http://")
