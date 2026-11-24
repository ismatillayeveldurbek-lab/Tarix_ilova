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
        "Noto'g'ri harf?;1;2;3;4;E;;;;\n"
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

    # muddati kelmasdan to'g'ri javob — quti o'zgarmaydi
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
