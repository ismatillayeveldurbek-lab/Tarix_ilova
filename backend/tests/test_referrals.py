"""Referal tizimi: qoidalar, bonuslar, bot va API."""
from sqlalchemy import func, select

from app.config import settings
from app.db import SessionLocal
from app.models import Question, Referral, XpBonus
from app.services.quiz import record_answer
from app.services.rating import user_rank, user_week_xp, weekly_leaderboard
from app.services.referrals import ensure_ref_code, parse_ref, register_referral
from app.services.users import get_or_create_user
from tests.test_services import load_sample


def test_parse_ref():
    assert parse_ref("ref_abc123") == "abc123"
    assert parse_ref("ref_") is None and parse_ref("hello") is None and parse_ref(None) is None
    assert parse_ref("ref_" + "x" * 40) is None


async def test_register_rules(session):
    inviter = await get_or_create_user(session, 1, "Ali")
    code = await ensure_ref_code(session, inviter)
    assert len(code) == 8 and await ensure_ref_code(session, inviter) == code  # kod o'zgarmaydi

    assert await register_referral(session, inviter, code) is None          # o'zini taklif qilish
    old = await get_or_create_user(session, 1, "Ali")                         # mavjud foydalanuvchi
    assert await register_referral(session, old, code) is None
    new = await get_or_create_user(session, 2, "Vali")
    assert await register_referral(session, new, "yoqkod") is None          # noma'lum kod
    r = await register_referral(session, new, code)
    assert r and r.inviter_id == inviter.id and new.referred_by == inviter.id
    assert await register_referral(session, new, code) is None              # ikkinchi marta emas


async def test_activation_and_rating_bonus(session):
    await load_sample(session)
    inviter = await get_or_create_user(session, 10, "Ali")
    friend = await get_or_create_user(session, 11, "Vali")
    await register_referral(session, friend, await ensure_ref_code(session, inviter))
    qs = list(await session.scalars(select(Question).limit(settings.referral_min_answers)))
    results = [await record_answer(session, friend, q, "z") for q in qs]  # hammasi xato — baribir hisoblanadi
    assert [bool(r.referral) for r in results] == [False] * (len(qs) - 1) + [True]
    assert await session.scalar(select(func.count()).select_from(XpBonus)) == 2

    # reyting: taklif qilgan hech savol yechmasa ham bonus XP bilan reytingda
    assert await user_week_xp(session, inviter.id) == settings.referral_xp_inviter
    assert await user_week_xp(session, friend.id) == settings.referral_xp_invited + len(qs) * 1
    board = await weekly_leaderboard(session)
    assert [r.user_id for r in board] == [inviter.id, friend.id]
    assert await user_rank(session, inviter.id) == 1

    # keyingi javoblarda bonus qayta berilmaydi
    again = await record_answer(session, friend, qs[0], "a")
    assert again.referral is None and await session.scalar(select(func.count()).select_from(XpBonus)) == 2


async def test_bot_referral_flow():
    from aiogram.methods import SendMessage
    from aiogram.types import User as TgUser
    from tests.test_bot_flow import cb, msg, setup

    bot, fake, dp = await setup()
    ali = TgUser(id=300, is_bot=False, first_name="Ali")
    vali = TgUser(id=301, is_bot=False, first_name="Vali")

    await dp.feed_update(bot, msg("/start", ali))
    await dp.feed_update(bot, msg("👥 Do'stlarni taklif qilish", ali))
    invite = [r for r in fake.requests if isinstance(r, SendMessage)][-1]
    assert "https://t.me/tarix_test_bot?start=ref_" in invite.text
    assert invite.reply_markup.inline_keyboard[0][0].url.startswith("https://t.me/share/url?")
    code = invite.text.split("start=ref_")[1].split()[0]

    await dp.feed_update(bot, msg(f"/start ref_{code}", vali))
    sent = [r for r in fake.requests if isinstance(r, SendMessage)]
    assert any(r.chat_id == 301 and "taklif qildi" in r.text for r in sent)
    assert any(r.chat_id == 300 and "havolangiz orqali qo'shildi" in r.text for r in sent)

    # Vali 5 ta savol yechadi -> Ali ga xabar va ikkalasiga bonus
    await dp.feed_update(bot, msg("📝 Test ishlash", vali))
    await dp.feed_update(bot, cb("qm:mixed", vali))
    for _ in range(settings.referral_min_answers):
        qid = int(fake.last_markup().inline_keyboard[0][0].callback_data.split(":")[1])
        await dp.feed_update(bot, cb(f"ans:{qid}:a", vali))
        await dp.feed_update(bot, cb("nxt", vali))
    sent = [r for r in fake.requests if isinstance(r, SendMessage)]
    assert any(r.chat_id == 300 and "sizga <b>+50 XP</b> qo'shildi" in r.text for r in sent)
    assert any(r.chat_id == 301 and "Taklif bonusi" in r.text for r in sent)

    # takroriy /start yangi taklif yaratmaydi
    await dp.feed_update(bot, msg(f"/start ref_{code}", vali))
    async with SessionLocal() as s:
        assert await s.scalar(select(func.count()).select_from(Referral)) == 1


async def test_api_referrals(seeded):
    from app.security import make_admin_token
    from tests.test_api import client, init_data

    async with client("tma " + init_data(600, "Ali")) as c:
        me = (await c.get("/api/referrals")).json()
        assert me["invited"] == 0 and "start=ref_" in me["link"] and me["min_answers"] == settings.referral_min_answers
    code = me["link"].split("ref_")[1]

    # Mini App havolasi orqali kirgan yangi foydalanuvchi (start_param)
    async with client("tma " + init_data(601, "Vali", start_param=f"ref_{code}")) as c:
        lesson = (await c.post("/api/lessons", json={"mode": "mixed"})).json()
        bonuses = []
        for q in lesson["questions"][: settings.referral_min_answers]:
            r = (await c.post("/api/answers", json={"lesson_id": lesson["lesson_id"], "question_id": q["id"], "option": "a"})).json()
            bonuses.append(r["referral_bonus"])
        assert bonuses[-1] == settings.referral_xp_invited and sum(bonuses) == bonuses[-1]

    async with client("tma " + init_data(600, "Ali")) as c:
        me = (await c.get("/api/referrals")).json()
        assert me["invited"] == 1 and me["active"] == 1 and me["earned_xp"] == settings.referral_xp_inviter
        assert me["friends"][0]["name"] == "Vali" and me["friends"][0]["active"]

    async with client("tma " + init_data(999)) as c:
        await c.get("/api/home")
    async with client("Bearer " + make_admin_token(999)) as c:
        stats = (await c.get("/api/admin/stats")).json()
        assert stats["referrals"]["total"] == 1 and stats["referrals"]["top"][0]["name"] == "Ali"
