"""Har bir xabar uchun bazaga ulanish ochadi va foydalanuvchini topadi.

Shu tufayli har bir handler `session` va `user` parametrlarini tayyor holda oladi.
"""
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.db import SessionLocal
from app.services.users import get_or_create_user


class DbUserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with SessionLocal() as session:
            tg_user = data.get("event_from_user")
            data["session"] = session
            data["user"] = (
                await get_or_create_user(session, tg_user.id, tg_user.full_name, tg_user.username)
                if tg_user else None
            )
            result = await handler(event, data)
            await session.commit()
            return result
