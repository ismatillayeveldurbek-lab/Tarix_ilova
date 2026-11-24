"""API uchun umumiy narsalar: baza sessiyasi va foydalanuvchini aniqlash.

Mini App har so'rovda `Authorization: tma <initData>` sarlavhasini yuboradi.
Brauzerdagi admin panel esa `Authorization: Bearer <token>` (bot /panel bergan) yuboradi.
"""
from typing import Annotated, AsyncIterator

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import SessionLocal
from app.models import User
from app.security import validate_init_data, verify_admin_token
from app.services.referrals import parse_ref, register_referral
from app.services.users import get_or_create_user


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


Session = Annotated[AsyncSession, Depends(get_session)]


async def current_user(
    session: Session, request: Request, authorization: Annotated[str | None, Header()] = None
) -> User:
    scheme, _, value = (authorization or "").partition(" ")
    if scheme.lower() == "tma" and value:
        tg = validate_init_data(value)
        if tg is None:
            raise HTTPException(401, "Telegram ma'lumoti noto'g'ri yoki eskirgan")
        name = " ".join(x for x in (tg.get("first_name"), tg.get("last_name")) if x)
        user = await get_or_create_user(session, int(tg["id"]), name, tg.get("username"))
        # Mini App referal havola orqali ochilgan bo'lsa (t.me/bot/app?startapp=ref_...)
        referral = await register_referral(session, user, parse_ref(tg.get("start_param")))
        await session.commit()
        bot = getattr(request.app.state, "bot", None)
        if referral and bot is not None:
            from app.bot.referral import notify_joined
            await notify_joined(bot, session, referral)
        return user
    if scheme.lower() == "bearer" and value:
        tid = verify_admin_token(value)
        user = await session.scalar(select(User).where(User.telegram_id == tid)) if tid else None
        if user is None or not user.is_admin:
            raise HTTPException(401, "Admin havolasi eskirgan. Botda /panel buyrug'ini qayta yuboring")
        return user
    if settings.dev_telegram_id:  # faqat kompyuterda sinash uchun
        user = await session.scalar(select(User).where(User.telegram_id == settings.dev_telegram_id))
        if user is None:
            user = await get_or_create_user(session, settings.dev_telegram_id, "Dev foydalanuvchi")
        await session.commit()
        return user
    raise HTTPException(401, "Ilovani Telegram orqali oching")


CurrentUser = Annotated[User, Depends(current_user)]


async def admin_user(user: CurrentUser) -> User:
    if not user.is_admin:
        raise HTTPException(403, "Faqat adminlar uchun")
    return user


AdminUser = Annotated[User, Depends(admin_user)]
