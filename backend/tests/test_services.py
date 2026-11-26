from datetime import date, timedelta

from sqlalchemy import func, select

from app.config import BASE_DIR
from app.db import utcnow
from app.models import Question, ReviewItem, Topic
from app.services.importer import import_file
from app.services.quiz import pick_question_ids, record_answer
from app.services.review import INTERVALS_DAYS, due_question_ids, update_review
from app.services.streak import touch_streak
from app.services.users import get_or_create_user


async def load_sample(session):
    path = BASE_DIR / "data" / "sample_questions.csv"
    return await import_file(session, path.name, path.read_bytes())


async def test_import_sample(session):
    report = await load_sample(session)
    assert report.added == 20 and not report.errors
    assert await session.scalar(select(func.count()).select_from(Topic)) > 0
    again = await load_sample(session)
    assert again.added == 0 and again.skipped_duplicates == 20


async def test_import_validation_semicolon_csv(session):
    csv_text = (
        "Savol;A;B;C;D;To'g'ri javob;Izoh;Mavzu;Davr;Qiyinlik\n"
        "Yaxshi savol?;1;2;3;4;b;izoh;M;D;o'rta\n"
        "Javobsiz savol?;1;2;3;4;;;;;\n"
        "Noto‘g‘ri harf?;1;2;3;4;E;;;;\n"
    )
    report = await import_file(session, "q.csv", csv_text.encode())
    assert report.added == 1
    assert len(report.errors) == 2
    q = await session.scalar(select(Question))
    assert q.correct_option == "b" and q.difficulty == 2


async def test_import_xlsx(session, tmp_path):
    from openpyxl import Workbook
    wb = Workbook()
    wb.active.append(["savol", "a", "b", "c", "d", "togri", "izoh", "mavzu", "davr", "qiyinlik"])
    wb.active.append(["Excel savoli?", "x", "y", "z", "w", "D", "", "T", "P", 3])
    path = tmp_path / "q.xlsx"
    wb.save(path)
    report = await import_file(session, "q.xlsx", path.read_bytes())
    assert report.added == 1


def test_streak():
    class U:
        streak_current = 0
        streak_best = 0
        last_active_date = None
    u = U()
    d = date(2026, 1, 10)
    assert touch_streak(u, d) and u.streak_current == 1
    assert not touch_streak(u, d)
    touch_streak(u, d + timedelta(days=1))
    assert u.streak_current == 2 and u.streak_best == 2
    touch_streak(u, d + timedelta(days=5))
    assert u.streak_current == 1 and u.streak_best == 2


async def test_review_leitner(session):
    await load_sample(session)
    user = await get_or_create_user(session, 1, "Test")
    qid = (await pick_question_ids(session, 1))[0]
    now = utcnow()

    await update_review(session, user.id, qid, False, now=now)
    item = await session.scalar(select(ReviewItem))
    assert item.box == 0 and item.next_review_at == now + timedelta(days=1)

    # muddati kelmasdan to‘g‘ri javob — quti o‘zgarmaydi
    await update_review(session, user.id, qid, True, now=now)
    assert item.box == 0

    t = now
    for expected_box in range(1, len(INTERVALS_DAYS)):
        t = item.next_review_at
        await update_review(session, user.id, qid, True, now=t)
        assert item.box == expected_box
    await update_review(session, user.id, qid, True, now=item.next_review_at)
    assert item.mastered

    # yana xato — boshidan
    await update_review(session, user.id, qid, False, now=t)
    assert item.box == 0 and not item.mastered


async def test_record_answer_adds_to_review(session):
    await load_sample(session)
    user = await get_or_create_user(session, 2, "Test")
    q = await session.get(Question, (await pick_question_ids(session, 1))[0])
    wrong = next(o for o in "abcd" if o != q.correct_option)
    res = await record_answer(session, user, q, wrong)
    assert not res.is_correct and res.streak_increased
    assert user.streak_current == 1
    item = await session.scalar(select(ReviewItem))
    item.next_review_at = utcnow() - timedelta(minutes=1)
    assert await due_question_ids(session, user.id, 10) == [q.id]


async def test_admin_from_env(session):
    admin = await get_or_create_user(session, 999, "Admin")
    user = await get_or_create_user(session, 5, "User")
    assert admin.is_admin and not user.is_admin


def test_effective_streak():
    from app.services.streak import effective_streak

    class U:
        streak_current = 5
        last_active_date = date(2026, 1, 10)
    assert effective_streak(U(), date(2026, 1, 10)) == 5
    assert effective_streak(U(), date(2026, 1, 11)) == 5  # bugun hali yechmagan — lekin uzilmagan
    assert effective_streak(U(), date(2026, 1, 12)) == 0  # bir kun o‘tkazib yuborildi


async def test_orphan_topics_in_path(session):
    from app.services.stats import learning_path
    csv_text = "savol,a,b,c,d,togri,mavzu\nDavrsiz savol?,1,2,3,4,A,Umumiy mavzu\n"
    await import_file(session, "q.csv", csv_text.encode())
    user = await get_or_create_user(session, 3, "T")
    path = await learning_path(session, user)
    assert path[-1]["id"] == 0 and path[-1]["topics"][0]["name"] == "Umumiy mavzu"


async def test_topic_progress_and_weak(session):
    from app.models import Answer
    from app.services.progress import overall_percent, recommendation, topic_progress, weak_topics

    await load_sample(session)
    user = await get_or_create_user(session, 50, "T")
    qs = list(await session.scalars(select(Question).order_by(Question.id)))
    by_topic: dict = {}
    for q in qs:
        by_topic.setdefault(q.topic_id, []).append(q)
    temur = max(by_topic.values(), key=len)  # "Amir Temur va Temuriylar" — 5 ta savol
    t0 = utcnow() - timedelta(hours=1)

    def add(q, ok, minutes):
        session.add(Answer(user_id=user.id, question_id=q.id, chosen_option="a", is_correct=ok,
                           answered_at=t0 + timedelta(minutes=minutes)))
    # 1-savol: avval xato, keyin to‘g‘ri -> o‘zlashtirilgan
    add(temur[0], False, 1); add(temur[0], True, 2)
    # 2-savol: avval to‘g‘ri, keyin xato -> o‘zlashtirilmagan
    add(temur[1], True, 3); add(temur[1], False, 4)
    # 3-savol: xato
    add(temur[2], False, 5)
    await session.flush()

    items = await topic_progress(session, user.id)
    t = next(i for i in items if i.id == temur[0].topic_id)
    assert (t.total, t.answered, t.mastered, t.attempts, t.correct) == (5, 3, 1, 5, 2)
    assert t.percent == 20 and t.accuracy == 40
    assert [w.id for w in weak_topics(items)] == [t.id]
    rec = recommendation(items)
    assert rec["kind"] == "weak" and rec["id"] == t.id
    assert overall_percent(items) == 5  # 1 / 20

    # 60 kundan eski javoblar aniqlikka kirmaydi (lekin o‘zlashtirishga kiradi)
    for a in await session.scalars(select(Answer).where(Answer.user_id == user.id)):
        a.answered_at = utcnow() - timedelta(days=90)
    await session.flush()
    t = next(i for i in await topic_progress(session, user.id) if i.id == temur[0].topic_id)
    assert t.attempts == 0 and t.mastered == 1 and t.accuracy is None


async def test_recommendation_new_topic(session):
    from app.services.progress import recommendation, topic_progress
    await load_sample(session)
    user = await get_or_create_user(session, 51, "T")
    rec = recommendation(await topic_progress(session, user.id))
    assert rec["kind"] == "new" and rec["answered"] == 0


async def test_import_normalizes_apostrophes(session):
    csv_text = "savol,a,b,c,d,togri,izoh,mavzu,davr\nQo'qon xonligiga kim asos solgan?,Olimxon,Shohruxbiy,Umarxon,X,B,1709-yil,O'zbek xonliklari,Yangi davr\n"
    r = await import_file(session, "q.csv", csv_text.encode())
    q = await session.scalar(select(Question))
    assert r.added == 1 and q.text == "Qo‘qon xonligiga kim asos solgan?" and q.topic.name == "O‘zbek xonliklari"
    # xuddi shu savol ‘ belgisi bilan — takroriy deb topiladi
    again = await import_file(session, "q.csv", csv_text.replace("Qo'qon", "Qo‘qon").encode())
    assert again.skipped_duplicates == 1


def test_normalize_db_url():
    from app.config import normalize_db_url
    neon = "postgresql://u:p@ep-x-pooler.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    assert normalize_db_url(neon) == (
        "postgresql+asyncpg://u:p@ep-x-pooler.eu-central-1.aws.neon.tech/neondb?ssl=require&prepared_statement_cache_size=0")
    assert normalize_db_url("postgres://u:p@h:5432/db") == "postgresql+asyncpg://u:p@h:5432/db"
    assert normalize_db_url("sqlite+aiosqlite:///x.db") == "sqlite+aiosqlite:///x.db"
    # Neon "Connect" oynasidan psql buyrug'i yoki qo'shtirnoq bilan nusxalangan
    assert normalize_db_url("psql 'postgresql://u:p@h/db?sslmode=require'") == "postgresql+asyncpg://u:p@h/db?ssl=require"
    assert normalize_db_url(' "postgres://u:p@h/db"\n') == "postgresql+asyncpg://u:p@h/db"


def test_bad_db_url_message_hides_value(monkeypatch):
    import pytest
    from pydantic import ValidationError

    from app.config import Settings
    monkeypatch.setenv("DATABASE_URL", "maxfiy-parol-bu-manzil-emas")
    with pytest.raises(ValidationError) as e:
        Settings(_env_file=None)
    assert "DATABASE_URL noto‘g‘ri" in str(e.value) and "maxfiy-parol" not in str(e.value)


def test_render_url_fallback(monkeypatch):
    from app.config import Settings
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://tarix.onrender.com")
    monkeypatch.delenv("WEBAPP_URL", raising=False)
    assert Settings(_env_file=None).webapp_url == "https://tarix.onrender.com"
    monkeypatch.setenv("WEBAPP_URL", "https://boshqa.uz")
    assert Settings(_env_file=None).webapp_url == "https://boshqa.uz"


async def test_reminder_times_cache(session):
    """Eslatma vazifasi faqat kimdir tanlagan daqiqada bazaga murojaat qiladi."""
    from datetime import time

    from app.models import User
    from app.services import reminder_times
    session.add(User(telegram_id=5001, full_name="A", reminder_time=time(20, 15)))
    await session.commit()
    try:
        times = await reminder_times.load(session)
        assert time(20, 15) in times and time(19, 0) in times
        assert reminder_times.may_be_due(time(20, 15)) and not reminder_times.may_be_due(time(3, 7))
        reminder_times.note(time(3, 7))
        assert reminder_times.may_be_due(time(3, 7))
    finally:
        reminder_times.reset()
    assert reminder_times.may_be_due(time(3, 8))  # yuklanmagan bo'lsa — har daqiqa tekshiriladi
