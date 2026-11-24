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


async def test_full_quiz_flow_in_cyrillic():
    bot, fake, dp = await setup()

    await dp.feed_update(bot, msg("/start"))
    assert "Alifboni tanlang" in fake.texts()[-1]

    await dp.feed_update(bot, cb("alph:cyrl"))
    assert "Тарих" in fake.texts()[-1]  # xush kelibsiz xabari kirillda

    await dp.feed_update(bot, msg("📝 Тест ишлаш"))  # menyu tugmasi kirillda
    assert fake.texts()[-1] == "Қандай тест ишлайсиз?"

    await dp.feed_update(bot, cb("qm:mixed"))
    correct_count = 0
    for i in range(10):
        q_markup = fake.last_markup()
        qid = int(q_markup.inline_keyboard[0][0].callback_data.split(":")[1])
        assert f"Савол {i + 1}/10" in fake.texts()[-1]
        # juft savollarga xato, toq savollarga to'g'ri javob beramiz
        from app.models import Question
        async with SessionLocal() as s:
            q = await s.get(Question, qid)
        choice = q.correct_option if i % 2 else next(o for o in "abcd" if o != q.correct_option)
        correct_count += i % 2
        await dp.feed_update(bot, cb(f"ans:{qid}:{choice}"))
        assert ("Тўғри" in fake.texts()[-1]) or ("Нотўғри" in fake.texts()[-1])
        assert "Изоҳ" in fake.texts()[-1]
        # A/B/C/D harflari lotinda qolishi kerak
        assert "<b>A)</b>" in fake.texts()[-1]

        # ikkinchi marta bosish qabul qilinmaydi
        await dp.feed_update(bot, cb(f"ans:{qid}:a"))
        assert isinstance(fake.requests[-1], AnswerCallbackQuery) and fake.requests[-1].show_alert

        await dp.feed_update(bot, cb("nxt"))

    assert "5/10" in fake.texts()[-1] and "50%" in fake.texts()[-1]
    async with SessionLocal() as s:
        assert await s.scalar(select(func.count()).select_from(Answer)) == 10
        assert await s.scalar(select(func.count()).select_from(ReviewItem)) == 5


async def test_report_flow_and_admin_view():
    bot, fake, dp = await setup()
    await dp.feed_update(bot, msg("/start"))
    await dp.feed_update(bot, cb("alph:latn"))
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


async def test_settings_switch_and_profile():
    bot, fake, dp = await setup()
    await dp.feed_update(bot, msg("/start"))
    await dp.feed_update(bot, cb("alph:latn"))
    await dp.feed_update(bot, msg("⚙️ Sozlamalar"))
    assert "Lotin" in fake.texts()[-1] and "19:00" in fake.texts()[-1]
    await dp.feed_update(bot, cb("set:alphabet"))
    assert "Алифбо" in fake.texts()[-1] or "Алифбо" in fake.texts()[-2]
    await dp.feed_update(bot, msg("👤 Профил"))
    assert "Жами жавоблар" in fake.texts()[-1]
