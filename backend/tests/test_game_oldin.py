"""4-bosqich: "Qaysi biri oldin?" — juftliklar, soat, ochko, XP, takrorlash."""
import random
from datetime import timedelta

import pytest
from sqlalchemy import func, select

from app.db import utcnow
from app.models import STATE_DUE, Fact, UserFactState, XpBonus
from app.services import game_oldin as g
from app.services.facts_import import import_facts, read_csv
from tests.test_facts import BAZA


@pytest.fixture
async def facts(session):
    await import_facts(session, read_csv(BAZA.read_bytes()))
    await session.commit()


async def test_make_pairs_real_baza(session, facts):
    pool = list(await session.scalars(select(Fact)))
    pairs = g.make_pairs(pool, rng=random.Random(1))
    assert len(pairs) == g.PAIRS
    by_id = {f.id: f for f in pool}
    ids = [x for p in pairs for x in p]
    assert len(ids) == len(set(ids))  # voqea takrorlanmaydi
    per_tier = g.PAIRS // len(g.TIERS)
    for i, (a, b) in enumerate(pairs):
        fa, fb = by_id[a], by_id[b]
        lo, hi = g.TIERS[min(i // per_tier, len(g.TIERS) - 1)]
        assert g.earlier_of(fa, fb) is not None  # vaqtlar kesishmaydi — javob bir ma'noli
        assert g.gap(fa, fb) >= lo and (hi is None or g.gap(fa, fb) <= hi), (i, g.gap(fa, fb))
        assert not any(ch.isdigit() for ch in fa.nom + fb.nom)  # yil kartada ko'rinmaydi
        assert g.eligible(fa) and g.eligible(fb)


def test_interval_and_ambiguity():
    from tests.test_cards import fact
    asr = fact(nom="Temuriylar davrida yer egaligi", sana_matn="XV asr", yil_boshi=1401)
    husayn = fact(nom="Sulton Husayn Mirzoning hokimiyatga kelishi", sana_matn="1458–1469-yillar", yil_boshi=1458, yil_oxiri=1469)
    elchi = fact(nom="Elchilar", sana_matn="1572, 1577-yillar", yil_boshi=1572)
    tunis = fact(nom="Tunisning zabt etilishi", sana_matn="1574-yil", yil_boshi=1574)
    davr = fact(nom="Usmonli elchisi", sana_matn="Shohmurod davri", yil_boshi=1785)
    dekada = fact(nom="Voqea", sana_matn="XV asrning 60-yillari", yil_boshi=1460)
    ming = fact(nom="Neolit", sana_matn="mil. avv. 6–4-mingyilliklar", yil_boshi=-6000)
    assert g.interval(asr) == (1401, 1500) and g.interval(dekada) == (1460, 1469)
    assert g.interval(elchi) == (1572, 1577) and g.interval(ming) == (-6000, -3001)
    assert g.interval(davr) is None and not g.eligible(davr)  # noaniq sana o'yinga kirmaydi
    # Mezondagi xato: kesishadigan vaqtlar juftlik bo'lmaydi
    assert g.earlier_of(asr, husayn) is None and g.earlier_of(elchi, tunis) is None
    assert g.earlier_of(ming, asr) == "a" and g.gap(ming, asr) == 1401 - (-3001)


def test_xp_rounds():
    assert g.xp_for_round(10, 1, 0)[0] == 30
    assert g.xp_for_round(10, 3, 0)[0] == 15
    assert g.xp_for_round(10, 4, 0)[0] == 0
    assert g.xp_for_round(24, 2, 90)[0] == 10  # kunlik 100 XP limiti
    assert g.multiplier(2) == 1 and g.multiplier(3) == 2 and g.multiplier(6) == 3


async def test_game_api_flow(session, facts, monkeypatch):
    from tests.test_api import client, init_data

    clock = {"now": utcnow()}
    monkeypatch.setattr(g, "utcnow", lambda: clock["now"])

    async def correct_pick(c, sid):
        # to'g'ri javobni bazadan aniqlaymiz (klientga yil yuborilmaydi)
        await session.close()
        s = await session.get(g.GameSession, sid)
        p = s.state["pairs"][s.state["idx"]]
        a, b = await session.get(Fact, p["a"]), await session.get(Fact, p["b"])
        return g.earlier_of(a, b)

    async with client("tma " + init_data(900)) as c:
        info = (await c.get("/api/v1/games/oldin")).json()
        assert info["rounds_today"] == 0 and info["xp_cap"] == 100

        st = (await c.post("/api/v1/games/oldin/start")).json()
        sid = st["session_id"]
        assert st["left_ms"] == 60_000 and st["pair"]["index"] == 1
        assert "year" not in st["pair"]["a"] and "source" not in st["pair"]["a"]  # javob yo'q

        points = []
        for i in range(4):  # 4 ta to'g'ri: 10, 10, 20 (x2), 20
            clock["now"] += timedelta(seconds=2)
            res = (await c.post(f"/api/v1/games/{sid}/answer", json={"pick": await correct_pick(c, sid)})).json()
            assert res["correct"] and res["a"]["year"] and res["a"]["source"]
            points.append(res["points"])
            # izoh o'qilayotganda soat to'xtagan: 30 soniya o'tsa ham vaqt kamaymaydi
            left = res["left_ms"]
            clock["now"] += timedelta(seconds=30)
            assert (await c.post(f"/api/v1/games/{sid}/answer", json={"pick": "a"})).status_code == 409
            nxt = (await c.post(f"/api/v1/games/{sid}/next")).json()
            assert nxt["left_ms"] == left
        assert points == [10, 10, 20, 20] and left == 60_000 - 8_000

        wrong = "b" if await correct_pick(c, sid) == "a" else "a"
        res = (await c.post(f"/api/v1/games/{sid}/answer", json={"pick": wrong})).json()
        assert not res["correct"] and res["combo"] == 0 and res["points"] == 0

        # sahifa yopildi — qayta "start" o'sha o'yinni davom ettiradi
        again = (await c.post("/api/v1/games/oldin/start")).json()
        assert again["session_id"] == sid and again["pair"]["index"] == 6 and again["score"] == 60

        # vaqt tugadi (52 soniya qolgan edi)
        clock["now"] += timedelta(seconds=60)
        assert (await c.post(f"/api/v1/games/{sid}/answer", json={"pick": "a"})).status_code == 409

        res = (await c.post(f"/api/v1/games/{sid}/finish")).json()
        assert (res["correct"], res["wrong"], res["score"], res["best_combo"]) == (4, 1, 60, 4)
        assert res["xp"] == 12 and res["accuracy"] == 80 and len(res["mistakes"]) == 1
        assert res["mistakes"][0]["a"]["year"]
        # takroriy finish XP'ni ikki marta bermaydi
        assert (await c.post(f"/api/v1/games/{sid}/finish")).json()["xp"] == 12

    uid = (await session.scalar(select(XpBonus))).user_id
    assert await session.scalar(select(func.sum(XpBonus.amount)).where(XpBonus.user_id == uid)) == 12
    states = list(await session.scalars(select(UserFactState).where(UserFactState.user_id == uid)))
    assert len(states) == 2 and all(s.holat == STATE_DUE for s in states)  # xato juftlik takrorlashga

    async with client("tma " + init_data(901)) as c:  # begona o'yin
        assert (await c.post(f"/api/v1/games/{sid}/finish")).status_code == 404


async def test_rounds_and_daily_cap(session, facts):
    from app.services.users import get_or_create_user

    user = await get_or_create_user(session, 950, "T")
    xps = []
    for _ in range(4):
        s = await g.start(session, user)
        st = {**s.state, "pairs": [{**p, "pick": "a", "ok": True} for p in s.state["pairs"]]}
        st["idx"] = len(st["pairs"])
        s.state = st
        xps.append((await g.finish(session, user, s))["xp"])
    # 24 to'g'ri × 3 = 72; 1-raund 72, 2-raund limitgacha 28, 3-raund 0 (limit), 4-raund 0
    assert xps == [72, 28, 0, 0]
    assert (await g.finish(session, user, s))["round"] == 4
