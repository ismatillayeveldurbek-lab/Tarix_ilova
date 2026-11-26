"""3-bosqich: kunlik takrorlash — kartochka tuzish, oraliqlar, API."""
from datetime import timedelta

from sqlalchemy import select

from app.db import utcnow
from app.models import STATE_DUE, STATE_LEARNING, STATE_MASTERED, Book, Fact, UserFactState
from app.services import srs
from app.services.cards import RECALL, back, card_ok, front
from app.services.facts_import import import_facts, read_csv
from tests.test_facts import BAZA, row, to_csv


def fact(**kw) -> Fact:
    d = {"id": "F-1", "tur": "sana", "nom": "Voqea", "matn": "Voqea bo‘lgan.", "sana_matn": "", "yil_boshi": None,
         "yil_oxiri": None, "asr": "", "davr": "Yangi", "hudud": "Jahon", "sinf": 8, "book_id": "K08J",
         "paragraf": "3-§", "mavzu_nomi": "Mavzu", "bet": "20", "iqtibos": "iqtibos", "shaxs_faoliyati": "",
         "shaxs_ishoralar": [], "urush_tomonlari": [], "golib": "", "natija": "", "joy_turi": "",
         "joy_hozirgi": "", "asar_muallifi": "", "ishonch": "yuqori", "izoh": ""}
    d.update(kw)
    f = Fact(**d)
    f.book = Book(id="K08J", sinf=8, fan="Jahon tarixi")
    return f


def shown(f: Fact) -> str:
    fr = front(f)
    return (fr["body"] + " " + " ".join(fr["hints"])).lower()


# ---------- Kartochka tuzish ----------

def test_front_never_contains_answer():
    s = fact(nom="1991-yil Mustaqillik e’lon qilinishi", sana_matn="1991-yil 31-avgust", yil_boshi=1991)
    assert front(s)["prompt"] == "Bu qachon bo‘lgan?" and "1991" not in shown(s)
    assert back(s)["answer"] == "1991-yil 31-avgust"

    a = fact(tur="atama", nom="Arxeolog", matn="Arxeologlar qazishma olib boradigan olimlar.")
    assert front(a)["prompt"] == "Qaysi atama?" and "arxeolog" not in shown(a) and back(a)["answer"] == "Arxeolog"

    sh = fact(tur="shaxs", nom="Amir Temur", shaxs_ishoralar=["Kesh yaqinida tug‘ilganman", "Temur tuzuklari menga nisbat beriladi", "Samarqand poytaxt"])
    assert "temur" not in shown(sh) and len(front(sh)["hints"]) == 3 and back(sh)["answer"] == "Amir Temur"

    asar = fact(tur="asar", nom="«Tarix» (Gerodot)", asar_muallifi="Gerodot")
    assert front(asar)["prompt"] == "Muallifi kim?" and "gerodot" not in shown(asar)

    joy = fact(tur="joy", joy_turi="shahar", nom="Memfis", matn="Memfis shahri Misr poytaxti bo‘lgan.")
    assert front(joy)["prompt"] == "Qaysi shahar?" and "memfis" not in shown(joy)

    # urush nomi g'olibni aytib qo'yadi -> "Qachon?" so'raladi, g'olib javobda
    u = fact(tur="urush", nom="Forslarning Misrni bosib olishi", sana_matn="mil. avv. 525-yil", yil_boshi=-525,
             golib="Forslar", urush_tomonlari=["Forslar", "Misr"], natija="Misr Fors davlatiga qo‘shildi.")
    assert front(u)["prompt"] == "Bu qachon bo‘lgan?" and "525" not in shown(u)
    assert "G‘olib: Forslar" in back(u)["extra"]


def test_recall_and_cloze_cards():
    r = fact(nom="Inklar dini", matn="Inklar Quyosh xudosiga sig‘inishgan.")
    assert front(r)["prompt"] == RECALL and back(r)["answer"] == r.matn and card_ok(r)
    c = fact(nom="Buyuk muzlik davri boshlanishi ilk paleolit oxirlari", sana_matn="ilk paleolit oxirlari",
             matn="Buyuk muzlik davri ilk paleolit oxirlarida boshlangan.")
    fr = front(c)
    assert fr["prompt"] == "Bo‘sh joyni to‘ldiring" and "paleolit" not in fr["body"].lower()


def test_card_ok_on_real_baza():
    import csv
    from app.services.facts_validation import check_row
    ok = total = 0
    for r in csv.DictReader(open(BAZA, encoding="utf-8")):
        d = check_row(r).data
        if d["ishonch"] == "past":
            continue
        f = fact(**{k: d[k] for k in ("tur", "nom", "matn", "sana_matn", "yil_boshi", "yil_oxiri", "asr", "golib",
                                       "natija", "joy_turi", "joy_hozirgi", "asar_muallifi", "shaxs_ishoralar",
                                       "urush_tomonlari", "shaxs_faoliyati")})
        total += 1
        ok += card_ok(f)
    assert total == 3840 and ok >= 3835  # javobi yashirib bo'lmaydigan bir nechta karta chetlatiladi


# ---------- Oraliqlar ----------

def test_schedule_intervals():
    now = utcnow()
    st = UserFactState(holat="yangi", step=0, correct_count=0, wrong_count=0)
    gaps, states = [], []
    for _ in range(5):
        srs.schedule(st, True, now)
        gaps.append(round((st.next_review_at - now) / timedelta(days=1)))
        states.append(st.holat)
    assert gaps == [1, 4, 10, 25, 60]
    assert states == [STATE_LEARNING] * 3 + [STATE_MASTERED] * 2
    srs.schedule(st, False, now)  # unutdi
    assert st.holat == STATE_DUE and st.step == 0 and st.next_review_at - now == timedelta(minutes=10)
    srs.schedule(st, True, now)
    assert st.holat == STATE_LEARNING and st.next_review_at - now == timedelta(days=1)


# ---------- API ----------

async def test_cards_api_flow(session):
    from tests.test_api import client, init_data

    rows = [row(id=f"S-{i:02}", nom=f"{1900 + i}-yil voqeasi", sana_matn=f"{1900 + i}-yil", yil_boshi=str(1900 + i), asr="XX")
            for i in range(25)]
    rows += [row(id="A-1", tur="atama", nom="Arxeolog", matn="Qazishma olib boradigan olim.", yil_boshi="", asr=""),
             row(id="H-1", ishonch="past")]
    await import_facts(session, read_csv(to_csv(rows)))
    await session.commit()

    async with client("tma " + init_data(800)) as c:
        q = (await c.get("/api/v1/cards")).json()
        assert len(q["cards"]) == 20 and q["new_left"] == 20  # kunlik yangi limit
        first = next(x for x in q["cards"] if x["fact_id"] == "S-00")
        assert set(first) == {"fact_id", "tur", "label", "prompt", "body", "hints", "davr", "sinf"}  # javob yo'q
        assert "1900" not in first["body"] and "H-1" not in [x["fact_id"] for x in q["cards"]]

        atama = (await c.get("/api/v1/cards", params={"tur": "atama"})).json()["cards"]
        assert [x["fact_id"] for x in atama] == ["A-1"]

        back_ = (await c.post(f"/api/v1/cards/{first['fact_id']}/reveal")).json()
        assert back_["answer"] == "1900-yil" and back_["source"] == "7-sinf Jahon tarixi, 5-§, 40-bet"

        g = (await c.post(f"/api/v1/cards/{first['fact_id']}/grade", json={"knew": False})).json()
        assert g["holat"] == "takrorlash_kerak" and g["today"] == {"cards_reviewed": 1, "new_cards": 1}
        for card in q["cards"]:
            if card["fact_id"] != first["fact_id"]:
                assert (await c.post(f"/api/v1/cards/{card['fact_id']}/grade", json={"knew": True})).status_code == 200

        # 20 ta yangi karta ko'rildi — navbatdan tashqaridagi 21-chisi qabul qilinmaydi
        outside = next(f"S-{i:02}" for i in range(25) if f"S-{i:02}" not in [x["fact_id"] for x in q["cards"]])
        assert (await c.post(f"/api/v1/cards/{outside}/grade", json={"knew": True})).status_code == 409
        assert (await c.post("/api/v1/cards/H-1/reveal")).status_code == 404
        s = (await c.get("/api/v1/cards/summary")).json()
        assert s["new_left"] == 0 and s["sections"]["sana"]["learning"] + s["sections"]["atama"]["learning"] == 20

    # "Bilmadim" bosilgan karta 10 daqiqadan keyin navbatning boshida
    st = await session.scalar(select(UserFactState).where(UserFactState.fact_id == first["fact_id"]))
    st.next_review_at = utcnow() - timedelta(minutes=1)
    await session.commit()
    async with client("tma " + init_data(800)) as c:
        q2 = (await c.get("/api/v1/cards")).json()
        assert [x["fact_id"] for x in q2["cards"]] == [first["fact_id"]] and q2["due"] == 1
        me = (await c.get("/api/v1/me")).json()
        assert me["facts"]["due_now"] == 1 and me["today"]["cards_reviewed"] == 20
