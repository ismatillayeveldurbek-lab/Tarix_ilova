"""1-bosqich: faktlar bazasi — tekshiruv, import, /api/v1/me, admin."""
import csv
import io

from sqlalchemy import func, select

from app.config import BASE_DIR
from app.db import utcnow
from app.models import STATE_DUE, STATE_MASTERED, Book, Fact, UserFactState
from app.services.facts_import import import_facts, read_csv
from app.services.facts_validation import book_from_id, century_of, check_row, clean_text

BAZA = BASE_DIR.parent / "data" / "baza.csv"
COLUMNS = ["id", "tur", "nom", "matn", "sana_matn", "yil_boshi", "yil_oxiri", "asr", "davr", "hudud", "sinf",
           "kitob_id", "paragraf", "mavzu_nomi", "bet", "iqtibos", "shaxs_faoliyati", "shaxs_ishoralar",
           "urush_tomonlari", "golib", "natija", "joy_turi", "joy_hozirgi", "asar_muallifi", "ishonch", "izoh"]


def row(**kw) -> dict:
    base = {c: "" for c in COLUMNS}
    base.update(id="T-1", tur="sana", nom="Voqea", matn="Voqea bo‘lgan.", yil_boshi="1336", asr="XIV",
                davr="O‘rta asrlar", hudud="Jahon", sinf="7", kitob_id="K07J", paragraf="5-§", bet="40",
                ishonch="yuqori")
    base.update(kw)
    return base


def to_csv(rows: list[dict]) -> bytes:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS)
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue().encode()


# ---------- Tekshiruv ----------

def test_clean_text():
    assert clean_text("O'zbekiston  va g'alaba") == "O‘zbekiston va g‘alaba"  # oddiy ' -> ‘
    assert clean_text("Oʻzbekiston") == "O‘zbekiston"                            # ʻ -> ‘
    assert clean_text("ma'no") == "ma’no"                                          # tutuq -> ’
    assert clean_text("««Avesto»» kitobi") == "«Avesto» kitobi"
    assert clean_text("O‘rta asrlar") == "O‘rta asrlar"  # to‘g‘ri belgi o‘zgarmaydi


def test_helpers():
    assert century_of(1336) == 14 and century_of(-329) == 4 and century_of(1900) == 19
    assert book_from_id("K08J") == (8, "Jahon tarixi")
    assert book_from_id("K10U") == (10, "O‘zbekiston tarixi")
    assert book_from_id("X1") is None


def test_check_row_flags():
    assert check_row(row()).flags == []
    assert "ishonch_past" in check_row(row(ishonch="past")).flags and check_row(row(ishonch="past")).hidden
    assert check_row(row(bet="")).hidden  # manbasiz fakt ko‘rsatilmaydi
    assert check_row(row(tur="boshqa")).hidden
    yoq = check_row(row(yil_boshi="", asr=""))
    assert yoq.flags == ["yil_yoq"] and not yoq.hidden
    assert "yil_asr_mos_emas" in check_row(row(yil_boshi="1500", asr="XIV")).flags
    assert check_row(row(yil_boshi="-329", asr="mil. avv. IV")).flags == []
    assert check_row(row(yil_boshi="-1400", asr="mil. avv. XIV–XIII")).flags == []
    assert "yil_xato" in check_row(row(yil_boshi="taxminan")).flags
    atama = check_row(row(tur="atama", nom="Arxeolog", matn="Arxeolog — qazishma olib boradigan olim.", yil_boshi="", asr=""))
    assert "atama_ozini_tushuntiradi" in atama.flags
    assert "kontekstsiz" in check_row(row(matn="Bu hududda mo‘g‘ul bosqini boshlandi.")).flags
    shaxs = check_row(row(tur="shaxs", shaxs_ishoralar="Hukmdor || Sarkarda"))
    assert "ishoralar_kam" in shaxs.flags and shaxs.data["shaxs_ishoralar"] == ["Hukmdor", "Sarkarda"]


# ---------- Import ----------

async def test_import_idempotent_and_admin_hidden_kept(session):
    rows = [row(id="T-1"), row(id="T-2", ishonch="past"), row(id="T-3", kitob_id="K09U")]
    r = await import_facts(session, read_csv(to_csv(rows)))
    assert (r.added, r.hidden, r.errors) == (3, 1, [])
    assert await session.scalar(select(func.count()).select_from(Book)) == 2

    f1 = await session.get(Fact, "T-1")
    assert f1.source == "7-sinf Jahon tarixi, 5-§, 40-bet" and f1.visible
    assert not (await session.get(Fact, "T-2")).visible
    f1.hidden_admin = True  # admin qo‘lda yashirdi
    await session.flush()

    r2 = await import_facts(session, read_csv(to_csv(rows)))
    assert (r2.added, r2.updated, r2.unchanged) == (0, 0, 3)
    assert (await session.get(Fact, "T-1")).hidden_admin  # import admin qarorini bekor qilmaydi

    # matn o‘zgardi + bitta fakt CSV’dan olib tashlandi
    r3 = await import_facts(session, read_csv(to_csv([row(id="T-1", matn="Yangi matn."), rows[1]])))
    assert r3.updated == 1 and r3.missing_in_csv == 1
    t3 = await session.get(Fact, "T-3")
    assert t3.hidden_import and "csvda_yoq" in t3.flags


async def test_import_errors(session):
    r = await import_facts(session, read_csv(to_csv([row(id=""), row(id="A"), row(id="A"), row(id="B", kitob_id="ZZ")])))
    assert r.added == 1 and len(r.errors) == 3
    try:
        read_csv(b"id,nom\n1,x\n")
        raise AssertionError("ustunlar tekshirilmadi")
    except ValueError as e:
        assert "tur" in str(e)


async def test_real_baza_csv(session):
    r = await import_facts(session, read_csv(BAZA.read_bytes()))
    assert r.total == 3987 and r.added == 3987 and not r.errors
    assert r.hidden == r.flags["ishonch_past"] == 147
    assert r.flags["yil_yoq"] == 339
    shaxs = await session.scalar(select(Fact).where(Fact.tur == "shaxs").limit(1))
    assert len(shaxs.shaxs_ishoralar) >= 3
    mil = await session.scalar(select(Fact).where(Fact.yil_boshi < 0, Fact.asr != "").limit(1))
    assert mil.yil_boshi < 0 and "mil. avv." in mil.asr


# ---------- API ----------

async def test_api_v1_me_and_admin(session):
    from app.security import make_admin_token
    from tests.test_api import client, init_data

    await import_facts(session, read_csv(to_csv([row(id=f"T-{i}") for i in range(5)] + [row(id="T-x", ishonch="past")])))
    await session.commit()

    async with client("tma " + init_data(700)) as c:
        me = (await c.get("/api/v1/me")).json()
        assert me["facts"] == {"total": 5, "yangi": 5, "organilmoqda": 0, "takrorlash_kerak": 0,
                               "ozlashtirildi": 0, "due_now": 0}
        assert me["today"]["xp"] == 0 and me["user"]["name"] == "Ali"
    uid = me["user"]["id"]
    session.add_all([
        UserFactState(user_id=uid, fact_id="T-0", holat=STATE_MASTERED),
        UserFactState(user_id=uid, fact_id="T-1", holat=STATE_DUE, next_review_at=utcnow()),
    ])
    await session.commit()
    async with client("tma " + init_data(700)) as c:
        f = (await c.get("/api/v1/me")).json()["facts"]
        assert (f["yangi"], f["ozlashtirildi"], f["takrorlash_kerak"], f["due_now"]) == (3, 1, 1, 1)
        assert (await c.get("/api/admin/facts")).status_code == 403

    async with client("tma " + init_data(999)) as c:
        await c.get("/api/home")
    async with client("Bearer " + make_admin_token(999)) as c:
        s = (await c.get("/api/admin/facts/summary")).json()
        assert s["total"] == 6 and s["visible"] == 5 and s["flags"] == {"ishonch_past": 1}
        assert s["books"][0]["title"] == "7-sinf Jahon tarixi"
        hidden = (await c.get("/api/admin/facts", params={"hidden": True})).json()
        assert [x["id"] for x in hidden["items"]] == ["T-x"]
        assert (await c.patch("/api/admin/facts/T-0", json={"hidden_admin": True})).json()["visible"] is False
        assert (await c.get("/api/admin/facts", params={"flag": "ishonch_past"})).json()["total"] == 1
        dry = (await c.post("/api/admin/import/facts", params={"dry_run": True},
                            files={"file": ("b.csv", to_csv([row(id="NEW")]))})).json()
        assert dry["added"] == 1
        assert (await c.get("/api/admin/facts/summary")).json()["total"] == 6  # dry-run yozmaydi
    async with client("tma " + init_data(700)) as c:
        assert (await c.get("/api/v1/me")).json()["facts"]["total"] == 4  # admin yashirgani hisoblanmaydi


async def test_api_v1_path(session):
    from tests.test_api import client, init_data

    rows = [row(id="A1", davr="Qadimgi"), row(id="A2", davr="Qadimgi", tur="shaxs", shaxs_ishoralar="a || b || c"),
            row(id="B1", davr="Yangi", tur="atama", yil_boshi="", asr=""), row(id="H", davr="Yangi", ishonch="past")]
    await import_facts(session, read_csv(to_csv(rows)))
    await session.commit()
    async with client("tma " + init_data(710)) as c:
        uid = (await c.get("/api/v1/me")).json()["user"]["id"]
    session.add(UserFactState(user_id=uid, fact_id="A1", holat=STATE_MASTERED))
    await session.commit()
    async with client("tma " + init_data(710)) as c:
        p = (await c.get("/api/v1/path")).json()
    assert p["total"] == 3 and p["mastered"] == 1
    assert p["davrlar"] == [{"name": "Qadimgi", "total": 2, "mastered": 1, "started": 1},
                            {"name": "Yangi", "total": 1, "mastered": 0, "started": 0}]  # yashirin fakt hisoblanmaydi
    assert [s["label"] for s in p["sections"]] == ["Yillar", "Shaxslar", "Atamalar"]
