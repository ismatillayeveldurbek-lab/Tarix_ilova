"""Botni Telegramga ulanmasdan sinash: so'rovlar soxta sessiyaga yoziladi."""
import itertools
from datetime import datetime

from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.methods import AnswerCallbackQuery, EditMessageText, SendMessage, TelegramMethod
from aiogram.types import CallbackQuery, Chat, InlineKeyboardMarkup, Message, Update, User as TgUser
from sqlalchemy import func, select

from app.bot.main import create_dispatcher
from app.db import SessionLocal
from app.models import Answer, QuestionReport, ReviewItem
from tests.test_services import load_sample

CHAT = Chat(id=100, type="private")
TG_USER = TgUser(id=100, is_bot=False, first_name="Ali")
_ids = itertools.count(1)


class FakeSession(BaseSession):
    def __init__(self):
        super().__init__()
        self.requests: list[TelegramMethod] = []

    async def make_request(self, bot, method, timeout=None):
        self.requests.append(method)
        if isinstance(method, (SendMessage, EditMessageText)):
            markup = getattr(method, "reply_markup", None)
            return Message(message_id=next(_ids), date=datetime.now(), chat=CHAT, text=method.text,
                           reply_markup=markup if isinstance(markup, InlineKeyboardMarkup) else None)
        return True

    async def close(self):
        pass

    async def stream_content(self, *a, **kw):
        yield b""

    def texts(self):
        return [r.text for r in self.requests if isinstance(r, (SendMessage, EditMessageText))]

    def last_markup(self):
        for r in reversed(self.requests):
            if isinstance(r, (SendMessage, EditMessageText)) and r.reply_markup is not None:
                return r.reply_markup


def msg(text: str, user: TgUser = TG_USER) -> Update:
    return Update(update_id=next(_ids), message=Message(
        message_id=next(_ids), date=datetime.now(), chat=CHAT, from_user=user, text=text))


def cb(data: str, user: TgUser = TG_USER) -> Update:
    m = Message(message_id=next(_ids), date=datetime.now(), chat=CHAT, text="x")
    return Update(update_id=next(_ids), callback_query=CallbackQuery(
        id=str(next(_ids)), from_user=user, chat_instance="ci", message=m, data=data))


DP = create_dispatcher()


async def setup():
    async with SessionLocal() as s:
        await load_sample(s)
        await s.commit()
    fake = FakeSession()
    bot = Bot("42:TEST", session=fake)
    DP.storage.storage.clear()  # har test toza FSM holatidan boshlansin
    return bot, fake, DP


async def test_full_quiz_flow():
    bot, fake, dp = await setup()

    await dp.feed_update(bot, msg("/start"))
    assert "Tarix — milliy sertifikatga tayyorgarlik" in fake.texts()[-1]

    await dp.feed_update(bot, msg("📝 Test ishlash"))
    assert fake.texts()[-1] == "Qanday test ishlaysiz?"

    await dp.feed_update(bot, cb("qm:mixed"))
    correct_count = 0
    for i in range(10):
        q_markup = fake.last_markup()
        qid = int(q_markup.inline_keyboard[0][0].callback_data.split(":")[1])
        assert f"Savol {i + 1}/10" in fake.texts()[-1]
        # juft savollarga xato, toq savollarga to'g'ri javob beramiz
        from app.models import Question
        async with SessionLocal() as s:
            q = await s.get(Question, qid)
        choice = q.correct_option if i % 2 else next(o for o in "abcd" if o != q.correct_option)
        correct_count += i % 2
        await dp.feed_update(bot, cb(f"ans:{qid}:{choice}"))
        edited = [r.text for r in fake.requests if isinstance(r, EditMessageText)][-1]
        assert ("To'g'ri" in edited) or ("Noto'g'ri" in edited)
        assert "Izoh" in edited
        # A/B/C/D harflari lotinda qolishi kerak
        assert "<b>A)</b>" in edited

        # ikkinchi marta bosish qabul qilinmaydi
        await dp.feed_update(bot, cb(f"ans:{qid}:a"))
        assert isinstance(fake.requests[-1], AnswerCallbackQuery) and fake.requests[-1].show_alert

        await dp.feed_update(bot, cb("nxt"))

    assert "5/10" in fake.texts()[-1] and "50%" in fake.texts()[-1]
    assert "+55 XP" in fake.texts()[-1]  # 5×10 + 5×1
    assert any("Kunlik maqsad bajarildi" in x for x in fake.texts())
    async with SessionLocal() as s:
        assert await s.scalar(select(func.count()).select_from(Answer)) == 10
        assert await s.scalar(select(func.count()).select_from(ReviewItem)) == 5


async def test_report_flow_and_admin_view():
    bot, fake, dp = await setup()
    await dp.feed_update(bot, msg("/start"))
    await dp.feed_update(bot, msg("📝 Test ishlash"))
    await dp.feed_update(bot, cb("qm:mixed"))
    qid = int(fake.last_markup().inline_keyboard[0][0].callback_data.split(":")[1])
    await dp.feed_update(bot, cb(f"ans:{qid}:a"))

    await dp.feed_update(bot, cb(f"rep:{qid}"))
    assert "xatoni qisqacha yozing" in fake.texts()[-1]
    await dp.feed_update(bot, msg("Javob noto'g'ri ko'rsatilgan"))
    assert "Rahmat" in fake.texts()[-2] or "Rahmat" in fake.texts()[-1]
    # adminga (id 999) xabar ketgan
    assert any(isinstance(r, SendMessage) and r.chat_id == 999 for r in fake.requests)

    async with SessionLocal() as s:
        report = await s.scalar(select(QuestionReport))
        assert report.comment == "Javob noto'g'ri ko'rsatilgan" and report.status == "new"

    # oddiy foydalanuvchi /admin ishlata olmaydi
    n = len(fake.requests)
    await dp.feed_update(bot, msg("/admin"))
    assert len(fake.requests) == n

    admin = TgUser(id=999, is_bot=False, first_name="Admin")
    await dp.feed_update(bot, msg("/reports", admin))
    assert "Javob noto'g'ri ko'rsatilgan" in fake.texts()[-1]
    await dp.feed_update(bot, cb(f"rs:fixed:{report.id}", admin))
    async with SessionLocal() as s:
        assert (await s.get(QuestionReport, report.id)).status == "fixed"


async def test_settings_and_profile():
    bot, fake, dp = await setup()
    await dp.feed_update(bot, msg("/start"))
    await dp.feed_update(bot, msg("⚙️ Sozlamalar"))
    assert "19:00" in fake.texts()[-1]
    await dp.feed_update(bot, cb("set:reminder"))
    assert "o'chirilgan" in fake.texts()[-1]
    await dp.feed_update(bot, msg("👤 Profil"))
    assert "Jami javoblar" in fake.texts()[-1]


async def test_review_daily_rating_history():
    bot, fake, dp = await setup()
    await dp.feed_update(bot, msg("/start"))

    await dp.feed_update(bot, msg("🔁 Xatolar ustida ishlash"))
    assert "takrorlash kerak bo'lgan savol yo'q" in fake.texts()[-1]

    await dp.feed_update(bot, msg("🔥 Kunlik 10 savol"))
    assert "Kunlik mashq" in fake.texts()[-2] and "Savol 1/10" in fake.texts()[-1]
    qid = int(fake.last_markup().inline_keyboard[0][0].callback_data.split(":")[1])
    from app.models import Question
    async with SessionLocal() as s:
        q = await s.get(Question, qid)
    wrong = next(o for o in "abcd" if o != q.correct_option)
    await dp.feed_update(bot, cb(f"ans:{qid}:{wrong}"))

    # xato savol takrorlashga tushdi; vaqtini o'tkazib yuboramiz
    from datetime import timedelta
    from app.db import utcnow
    async with SessionLocal() as s:
        item = await s.scalar(select(ReviewItem))
        item.next_review_at = utcnow() - timedelta(minutes=1)
        await s.commit()
    await dp.feed_update(bot, msg("🔁 Xatolar ustida ishlash"))
    assert "1 ta savol" in fake.texts()[-2]

    await dp.feed_update(bot, msg("🏆 Reyting"))
    assert "Haftalik reyting" in fake.texts()[-1] and "1 XP" in fake.texts()[-1]

    await dp.feed_update(bot, msg("/bugun"))
    assert "Tarixda bugun" in fake.texts()[-1] or "voqea kiritilmagan" in fake.texts()[-1]


async def test_scheduler_reminder_and_history(monkeypatch):
    from datetime import date, datetime, time as dtime
    from app.bot import scheduler
    from app.config import settings
    from app.models import HistoryEvent, User

    bot, fake, dp = await setup()
    await dp.feed_update(bot, msg("/start"))
    async with SessionLocal() as s:
        s.add(HistoryEvent(month=4, day=9, year=1336, title="Amir Temur tavalludi", text="..."))
        await s.commit()

    now = datetime(2026, 4, 9, 19, 0, tzinfo=settings.tz)
    assert await scheduler.send_reminders(bot, now) == 1
    assert "sizni kutmoqda" in fake.texts()[-1]
    assert await scheduler.send_reminders(bot, now) == 0  # shu kuni qayta yuborilmaydi

    monkeypatch.setattr(scheduler, "local_today", lambda: date(2026, 4, 9))
    monkeypatch.setattr(settings, "channel_id", "@test_kanal")
    assert await scheduler.post_history_today(bot) == 1
    assert any(isinstance(r, SendMessage) and r.chat_id == "@test_kanal" for r in fake.requests)
    assert "Amir Temur" in fake.texts()[-1]
    assert await scheduler.post_history_today(bot) == 0  # ikki marta yuborilmaydi


async def test_bot_sends_question_image():
    from aiogram.methods import SendPhoto
    from app.models import Media, Question
    bot, fake, dp = await setup()
    async with SessionLocal() as s:
        m = Media(mime="image/png", data=b"\x89PNG\r\n\x1a\nxx")
        s.add(m)
        await s.flush()
        for q in (await s.scalars(select(Question))):
            q.image_url = f"/api/media/{m.id}"
        await s.commit()
    await dp.feed_update(bot, msg("/start"))
    await dp.feed_update(bot, msg("📝 Test ishlash"))
    await dp.feed_update(bot, cb("qm:mixed"))
    assert any(isinstance(r, SendPhoto) for r in fake.requests)
    assert "Savol 1/10" in fake.texts()[-1]  # rasmdan keyin savol ham keldi


async def test_profile_shows_weak_topics():
    from datetime import timedelta
    from app.db import utcnow
    from app.models import Answer, Question, User
    bot, fake, dp = await setup()
    await dp.feed_update(bot, msg("/start"))
    async with SessionLocal() as s:
        user = await s.scalar(select(User).where(User.telegram_id == 100))
        q = await s.scalar(select(Question).order_by(Question.id))
        for i in range(3):
            s.add(Answer(user_id=user.id, question_id=q.id, chosen_option="a", is_correct=False,
                         answered_at=utcnow() - timedelta(minutes=i)))
        await s.commit()
    await dp.feed_update(bot, msg("👤 Profil"))
    sent = [r for r in fake.requests if isinstance(r, SendMessage)][-1]
    assert "Zaif mavzular" in sent.text and "O'zlashtirish" in sent.text.replace("o'zlashtirish", "O'zlashtirish")
    button = sent.reply_markup.inline_keyboard[0][0]
    assert button.callback_data.startswith("tp:") and "0%" in button.text
    await dp.feed_update(bot, cb(button.callback_data))  # tugma mavzu testini boshlaydi
    assert "Savol 1/" in fake.texts()[-1]
