"""Faktlardan test savollari: sifat qoidalari, bazaga yozish va API."""
import re

from sqlalchemy import select

from app.models import Fact, Question
from app.services.facts_import import import_facts, read_csv
from app.services.game_oldin import interval
from app.services.question_gen import date_shape, generate, question_leaks, sync_questions
from tests.test_facts import BAZA, row, to_csv


def _years() -> list[dict]:
    """Bir xil shakldagi ("1336-yil") va bir-biridan uzoq sanalar."""
    return [row(id=f"S-{i:02}", nom=f"Voqea {chr(65 + i)} sodir bo‘lishi", sana_matn=f"{1300 + i * 12}-yil",
                yil_boshi=str(1300 + i * 12), asr="XIV", matn=f"{1300 + i * 12}-yilda voqea {chr(65 + i)} bo‘lgan.")
            for i in range(8)]


def _people() -> list[dict]:
    names = ["Amir Temur", "Mirzo Ulug‘bek", "Shohruh Mirzo", "Husayn Boyqaro", "Bobur Mirzo"]
    return [row(id=f"P-{i}", tur="shaxs", nom=n, matn=f"{n} — Temuriylar davri hukmdori.", shaxs_faoliyati="hukmdor",
                yil_boshi="", asr="", shaxs_ishoralar=f"{n.split()[0]} nomi bilan mashhurman || {i + 1}-farzandman || Hukmdor bo‘lganman")
            for i, n in enumerate(names)]


async def _load(session, rows):
    await import_facts(session, read_csv(to_csv(rows)))
    await session.commit()
    return list(await session.scalars(select(Fact)))


async def test_when_questions(session):
    facts = await _load(session, _years())
    qs = [q for q in generate(facts) if q.kind == "qachon"]
    assert len(qs) == 8
    by_id = {f.id: f for f in facts}
    for q in qs:
        assert q.asks_time and len(set(q.options)) == 4 and q.correct in "abcd"
        assert not question_leaks(q) and not re.search(r"\d", q.text)
        assert {date_shape(o) for o in q.options} == {"yil"}  # bir xil shakl
        # variantlar oraliqlari kesishmaydi
        ivs = sorted(interval(next(f for f in by_id.values() if f.sana_matn == o)) for o in q.options)
        assert all(a[1] < b[0] for a, b in zip(ivs, ivs[1:]))
        assert "Manba: 7-sinf Jahon tarixi" in q.explanation  # izohda manba


async def test_who_question_hides_name(session):
    facts = await _load(session, _people())
    q = next(q for q in generate(facts) if q.key == "P-0:kim")
    assert q.text.startswith("Kim men?") and "Amir" not in q.text and "…" in q.text
    assert q.options["abcd".index(q.correct)] == "Amir Temur" and not q.asks_time


async def test_bad_facts_skipped(session):
    rows = _years() + [
        row(id="X-1", nom="1991-yil Mustaqillik", sana_matn="1991-yil", yil_boshi="1991"),   # yil nomda
        row(id="X-2", nom="Inklarning XV asrdagi istilolari", sana_matn="XV asr", yil_boshi="1401"),  # asr nomda
        row(id="X-3", ishonch="past"),                                                       # yashirilgan
    ]
    facts = await _load(session, rows)
    keys = {q.key for q in generate(facts)}
    assert not {"X-1:qachon", "X-2:qachon", "X-3:qachon"} & keys


async def test_sync_idempotent_locked_and_deactivate(session):
    await _load(session, _years() + _people())
    r1 = await sync_questions(session)
    await session.commit()
    assert r1.added == r1.total > 0
    r2 = await sync_questions(session)
    assert r2.added == r2.updated == 0 and r2.unchanged == r1.total

    q = await session.scalar(select(Question).where(Question.gen_key == "S-00:qachon"))
    assert q.topic and q.period and q.period.name == "O‘rta asrlar"
    q.text, q.locked = "Admin tahrirlagan savol", True
    hidden = await session.get(Fact, "P-0")
    hidden.hidden_admin = True
    await session.commit()

    r3 = await sync_questions(session)
    await session.commit()
    assert r3.locked == 1 and r3.deactivated >= 1
    assert (await session.scalar(select(Question).where(Question.gen_key == "S-00:qachon"))).text == "Admin tahrirlagan savol"
    assert not (await session.scalar(select(Question).where(Question.gen_key == "P-0:kim"))).is_active


async def test_lesson_hides_era_for_time_questions(session):
    from tests.test_api import client, init_data
    await _load(session, _years())
    await sync_questions(session)
    await session.commit()
    async with client("tma " + init_data(900)) as c:
        r = (await c.post("/api/lessons", json={"mode": "mixed"})).json()
        assert r["questions"]
        for q in r["questions"]:
            assert q["period"] is None and q["topic"] is None  # vaqt savoli: davr va mavzu yo'q
            assert "correct_option" not in q                   # javob oldindan yuborilmaydi


async def test_real_base_quality(session):
    """Haqiqiy baza: ko'p savol tuziladi, hech birida javob sizmaydi, variantlar takrorlanmaydi."""
    if not BAZA.exists():
        return
    await import_facts(session, read_csv(BAZA.read_bytes()))
    await session.commit()
    qs = generate(list(await session.scalars(select(Fact))))
    assert len(qs) > 3000
    assert not [q.key for q in qs if question_leaks(q)]
    assert all(len({o.lower() for o in q.options}) == 4 for q in qs)
    assert all(q.asks_time == (q.kind == "qachon") for q in qs)



async def test_admin_filters_and_hard_sort(session):
    """Admin: avtomatik / tahrirlangan / qo'lda filtri va eng ko'p adashilgan savollar."""
    from app.models import Answer, User
    from app.security import make_admin_token
    from tests.test_api import client

    await _load(session, _years())
    await sync_questions(session)
    session.add(Question(text="Qo‘lda savol", option_a="1", option_b="2", option_c="3", option_d="4", correct_option="a"))
    u = User(telegram_id=5005, full_name="O‘quvchi")
    session.add_all([u, User(telegram_id=999, full_name="Admin", is_admin=True)])
    await session.flush()
    hard = await session.scalar(select(Question).where(Question.gen_key == "S-03:qachon"))
    easy = await session.scalar(select(Question).where(Question.gen_key == "S-04:qachon"))
    hard.locked = True
    for i in range(4):
        session.add(Answer(user_id=u.id, question_id=hard.id, chosen_option="a", is_correct=i == 0))
        session.add(Answer(user_id=u.id, question_id=easy.id, chosen_option="a", is_correct=True))
    await session.commit()

    async with client("Bearer " + make_admin_token(999)) as c:
        get = lambda **p: c.get("/api/admin/questions", params=p)  # noqa: E731
        r0 = (await get(source="manual")).json()
        assert r0.get("total") == 1, r0
        assert (await get(source="edited")).json()["total"] == 1
        assert (await get(source="auto")).json()["total"] == 7
        r = (await get(sort="hard")).json()
        assert [x["id"] for x in r["items"]] == [hard.id, easy.id]
        assert r["items"][0]["accuracy"] == 25 and r["items"][0]["answers"] == 4 and r["items"][0]["locked"]


async def test_import_topic_tests_with_source_and_time_flag(session):
    """Mavzu testlari CSV'si (docs/promptlar/07-mavzu-testlari.md formati)."""
    from app.services.importer import import_file
    csv_text = (
        "savol,a,b,c,d,togri,izoh,manba,mavzu,davr,qiyinlik,vaqt_savoli\n"
        "\"Amir Temur qachon taxtga o‘tirgan?\",\"1360-yil\",\"1370-yil\",\"1380-yil\",\"1405-yil\",B,"
        "\"1370-yilda Balxda qurultoy bo‘lgan.\",\"7-sinf O‘zbekiston tarixi, 12-§, 85-bet\",\"Amir Temur davlati\",\"O‘rta asrlar\",2,ha\n"
        "\"Temur tuzuklari kimga nisbat beriladi?\",\"Amir Temur\",\"Bobur\",\"Ulug‘bek\",\"Navoiy\",A,"
        "\"Tuzuklar Amir Temurga nisbat beriladi.\",\"7-sinf O‘zbekiston tarixi, 12-§, 88-bet\",\"Amir Temur davlati\",\"O‘rta asrlar\",1,yo‘q\n"
    ).encode()
    rep = await import_file(session, "testlar.csv", csv_text)
    await session.commit()
    assert rep.added == 2 and not rep.errors
    when, who = list(await session.scalars(select(Question).order_by(Question.id)))
    assert when.asks_time and not who.asks_time
    assert when.explanation.endswith("Manba: 7-sinf O‘zbekiston tarixi, 12-§, 85-bet")
    assert when.topic.name == "Amir Temur davlati" and when.period.name == "O‘rta asrlar"
