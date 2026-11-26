"""5-bosqich: yagona XP, kunlik faollik, seriya va limitlar."""
from datetime import timedelta

from sqlalchemy import func, select

from app.db import local_today
from app.models import DailyStat, Fact, Question, XpBonus
from app.services import srs, xp
from app.services.facts import get_daily_stat
from app.services.facts_import import import_facts, read_csv
from app.services.quiz import record_answer
from app.services.rating import user_week_xp
from app.services.users import get_or_create_user
from tests.test_facts import row, to_csv
from tests.test_services import load_sample


async def test_sources_actions_and_card_cap(session):
    await load_sample(session)
    await import_facts(session, read_csv(to_csv([row(id=f"F-{i:02}", nom=f"Voqea {chr(65 + i)}") for i in range(35)])))
    user = await get_or_create_user(session, 1200, "T")

    q = await session.scalar(select(Question))
    await record_answer(session, user, q, q.correct_option)   # test: +10 XP, 1 faollik
    await record_answer(session, user, q, "z")                # test: +1 XP
    srs.NEW_PER_DAY = 100                                     # limitni bu test uchun oshiramiz
    try:
        for f in await session.scalars(select(Fact).order_by(Fact.id).limit(32)):
            await srs.grade(session, user, f, knew=True)       # karta: +2 XP, kuniga 60 gacha
    finally:
        srs.NEW_PER_DAY = 20

    stat = await get_daily_stat(session, user.id)
    assert stat.game_xp == {"test": 11, "kartochka": 60}     # 32 × 2 = 64 -> 60 (limit)
    assert stat.xp == 71 and stat.actions == 34
    # reyting: test — javoblardan, kartochka — XpBonus'dan; ikki marta sanalmaydi
    assert await session.scalar(select(func.sum(XpBonus.amount))) == 60
    assert await user_week_xp(session, user.id) == 71


async def test_cards_alone_keep_streak(session):
    await import_facts(session, read_csv(to_csv([row(id="F-1")])))
    user = await get_or_create_user(session, 1201, "T")
    user.streak_current, user.streak_best, user.last_active_date = 4, 4, local_today() - timedelta(days=1)
    await srs.grade(session, user, await session.get(Fact, "F-1"), knew=False)
    assert user.streak_current == 5 and user.last_active_date == local_today()


async def test_new_day_resets_limits(session):
    await import_facts(session, read_csv(to_csv([row(id="F-1")])))
    user = await get_or_create_user(session, 1202, "T")
    await xp.award(session, user.id, 70, "kartochka", cap=xp.CARD_XP_CAP)
    stat = await get_daily_stat(session, user.id)
    assert stat.game_xp["kartochka"] == 60
    stat.day = local_today() - timedelta(days=1)  # kecha bo'lgan deb faraz qilamiz
    await session.flush()
    assert await xp.award(session, user.id, 10, "kartochka", cap=xp.CARD_XP_CAP) == 10  # bugun yangidan
    assert await session.scalar(select(func.count()).select_from(DailyStat)) == 2


async def test_api_me_xp_breakdown(session):
    from tests.test_api import client, init_data

    await import_facts(session, read_csv(to_csv([row(id=f"F-{i}") for i in range(3)])))
    await session.commit()
    async with client("tma " + init_data(1300)) as c:
        for fid in ("F-0", "F-1", "F-2"):
            await c.post(f"/api/v1/cards/{fid}/grade", json={"knew": True})
        me = (await c.get("/api/v1/me")).json()
        assert me["today"]["xp"] == 6 and me["today"]["actions"] == 3 and me["today"]["goal"] == 10
        assert me["today"]["xp_by_source"] == [{"source": "kartochka", "label": "Kartochkalar", "xp": 6}]
        assert me["week_xp"] == 6 and me["user"]["streak"] == 1
        home = (await c.get("/api/home")).json()
        assert home["today"]["done"] == 3  # kunlik maqsad: test + karta + o'yin
