from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import User


async def get_or_create_user(
    session: AsyncSession, telegram_id: int, full_name: str = "", username: str | None = None
) -> User:
    user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    if user is None:
        user = User(telegram_id=telegram_id, full_name=full_name, username=username)
        session.add(user)
    else:
        user.full_name = full_name or user.full_name
        user.username = username
        user.is_blocked = False
    user.is_admin = user.is_admin or telegram_id in settings.admin_id_list
    await session.flush()
    return user
