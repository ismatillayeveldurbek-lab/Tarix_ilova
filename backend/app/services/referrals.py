"""Referal (taklif) tizimi.

1. Har bir foydalanuvchining shaxsiy kodi bor: t.me/<bot>?start=ref_<kod>
2. Havola orqali kelgan YANGI foydalanuvchi taklif qilgan kishiga bog'lanadi.
   (Botda avvaldan bor foydalanuvchilar va o'zini o'zi taklif qilish hisoblanmaydi.)
3. Do'st REFERRAL_MIN_ANSWERS ta savol yechgach, taklif "faol" bo'ladi va ikkalasiga XP bonus beriladi.
"""
import secrets

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import utcnow
from app.models import Answer, Referral, User, XpBonus

CODE_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"  # adashtiradigan belgilar (0/o, 1/l/i) yo'q
CODE_LENGTH = 8


def new_code() -> str:
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


async def ensure_ref_code(session: AsyncSession, user: User) -> str:
    if not user.ref_code:
        while True:
            code = new_code()
            if not await session.scalar(select(User.id).where(User.ref_code == code)):
                break
        user.ref_code = code
        await session.flush()
    return user.ref_code


def parse_ref(arg: str | None) -> str | None:
    """"/start ref_abc123" yoki Mini App start_param "ref_abc123" -> "abc123"."""
    if arg and arg.startswith("ref_") and 4 < len(arg) <= 4 + 16:
        return arg[4:]
    return None


def referral_link(bot_username: str, code: str) -> str:
    return f"https://t.me/{bot_username or 'bot'}?start=ref_{code}"


async def register_referral(session: AsyncSession, invited: User, code: str | None) -> Referral | None:
    """Yangi foydalanuvchini taklif qilgan kishiga bog'laydi. Shartlar bajarilmasa None."""
    if not code or not getattr(invited, "is_new", False):
        return None
    inviter = await session.scalar(select(User).where(User.ref_code == code))
    if inviter is None or inviter.id == invited.id:
        return None
    if await session.scalar(select(Referral.id).where(Referral.invited_id == invited.id)):
        return None
    invited.referred_by = inviter.id
    referral = Referral(inviter_id=inviter.id, invited_id=invited.id)
    session.add(referral)
    await session.flush()
    return referral


async def try_activate(session: AsyncSession, user: User) -> Referral | None:
    """Do'st yetarli savol yechgan bo'lsa, taklifni faollashtirib, bonuslarni beradi."""
    referral = await session.scalar(
        select(Referral).where(Referral.invited_id == user.id, Referral.activated_at.is_(None))
    )
    if referral is None:
        return None
    answers = await session.scalar(select(func.count()).select_from(Answer).where(Answer.user_id == user.id))
    if answers < settings.referral_min_answers:
        return None
    referral.activated_at = utcnow()
    session.add_all([
        XpBonus(user_id=referral.inviter_id, amount=settings.referral_xp_inviter, reason="referral"),
        XpBonus(user_id=user.id, amount=settings.referral_xp_invited, reason="referral_welcome"),
    ])
    await session.flush()
    return referral


async def referral_stats(session: AsyncSession, user: User) -> dict:
    rows = (await session.execute(
        select(User.full_name, Referral.created_at, Referral.activated_at)
        .join(User, User.id == Referral.invited_id)
        .where(Referral.inviter_id == user.id).order_by(Referral.created_at.desc())
    )).all()
    earned = await session.scalar(
        select(func.coalesce(func.sum(XpBonus.amount), 0))
        .where(XpBonus.user_id == user.id, XpBonus.reason == "referral")
    )
    return {
        "invited": len(rows),
        "active": sum(1 for r in rows if r.activated_at),
        "earned_xp": int(earned or 0),
        "friends": [
            {"name": name or "Foydalanuvchi", "joined_at": created.isoformat() + "Z", "active": activated is not None}
            for name, created, activated in rows
        ],
    }
