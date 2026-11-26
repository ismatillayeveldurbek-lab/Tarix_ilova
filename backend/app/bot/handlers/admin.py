"""Admin bo‘limi: statistika, xato xabarlari, savollarni import qilish."""
from aiogram import Bot, F, Router
from aiogram.filters import Command, Filter
from aiogram.types import (
    CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, Message, TelegramObject,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards import report_admin_kb, webapp
from app.bot.utils import esc
from app.config import BASE_DIR, settings
from app.security import make_admin_token
from app.models import Question, QuestionReport, User
from app.services.importer import import_file

MAX_FILE_MB = 10


class IsAdmin(Filter):
    async def __call__(self, event: TelegramObject, user: User | None = None) -> bool:
        return bool(user and user.is_admin)


router = Router(name="admin")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

HELP = (
    "🛠 <b>Admin panel</b>\n\n"
    "👥 Foydalanuvchilar: <b>{users}</b>\n"
    "❓ Faol savollar: <b>{questions}</b>\n"
    "⚠️ Yangi xato xabarlari: <b>{reports}</b>\n\n"
    "<b>Buyruqlar:</b>\n"
    "/panel — 🖥 veb admin panel (savollar, import, imtihon formati...)\n"
    "/reports — yangi xato xabarlarini ko‘rish\n"
    "/shablon — import uchun namuna CSV fayl\n"
    "📎 Savollarni qo‘shish: .xlsx yoki .csv faylni shu chatga yuboring"
)


@router.message(Command("admin"))
async def admin_home(message: Message, session: AsyncSession) -> None:
    users = await session.scalar(select(func.count()).select_from(User))
    questions = await session.scalar(
        select(func.count()).select_from(Question).where(Question.is_active.is_(True))
    )
    reports = await session.scalar(
        select(func.count()).select_from(QuestionReport).where(QuestionReport.status == "new")
    )
    await message.answer(HELP.format(users=users, questions=questions, reports=reports))


@router.message(Command("panel"))
async def admin_panel(message: Message, user: User) -> None:
    if not settings.webapp_url:
        await message.answer(
            "🖥 Admin panel ilova bilan birga ishlaydi. Avval .env faylida WEBAPP_URL ni kiriting "
            "(masalan, https://sizning-domeningiz)."
        )
        return
    token = make_admin_token(user.telegram_id)
    url = settings.webapp_url.rstrip("/") + f"/#/admin?token={token}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🖥 Brauzerda ochish (kompyuter uchun qulay)", url=url)],
        [InlineKeyboardButton(text="📱 Telegram ichida ochish", web_app=webapp("admin"))],
    ])
    await message.answer(
        "🛠 <b>Admin panel</b>\n\nBrauzer havolasi 12 soat amal qiladi. Uni hech kimga yubormang!",
        reply_markup=kb,
    )


@router.message(Command("reports"))
async def list_reports(message: Message, session: AsyncSession) -> None:
    reports = list(await session.scalars(
        select(QuestionReport).where(QuestionReport.status == "new")
        .order_by(QuestionReport.created_at).limit(10)
    ))
    if not reports:
        await message.answer("✅ Yangi xato xabarlari yo‘q.")
        return
    for r in reports:
        q = r.question
        await message.answer(
            f"⚠️ <b>#{r.id}</b> · savol #{q.id}\n"
            f"{esc(q.text)}\n"
            f"A) {esc(q.option_a)}\nB) {esc(q.option_b)}\nC) {esc(q.option_c)}\nD) {esc(q.option_d)}\n"
            f"To‘g‘ri: <b>{q.correct_option.upper()}</b>\n\n"
            f"💬 {esc(r.comment)}\n👤 {esc(r.user.full_name)}",
            reply_markup=report_admin_kb(r.id),
        )


@router.callback_query(F.data.startswith("rs:"))
async def resolve_report(cb: CallbackQuery, session: AsyncSession) -> None:
    _, action, rid = cb.data.split(":")
    report = await session.get(QuestionReport, int(rid))
    if report is None:
        await cb.answer("Topilmadi", show_alert=True)
        return
    if action == "off":
        report.question.is_active = False
        report.status = "fixed"
        label = "🚫 Savol o‘chirildi"
    else:
        report.status = action
        label = "✅ Tuzatildi deb belgilandi" if action == "fixed" else "❌ Rad etildi"
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.message.reply(label)
    await cb.answer()


@router.message(Command("shablon"))
async def send_template(message: Message) -> None:
    await message.answer_document(
        FSInputFile(BASE_DIR / "data" / "sample_questions.csv"),
        caption="Namuna fayl. Ustunlar: savol, a, b, c, d, togri, izoh, mavzu, davr, qiyinlik",
    )


@router.message(F.document)
async def import_document(message: Message, session: AsyncSession, bot: Bot) -> None:
    doc = message.document
    name = (doc.file_name or "").lower()
    if not name.endswith((".csv", ".xlsx")):
        await message.answer("Faqat .xlsx yoki .csv fayl yuboring.")
        return
    if (doc.file_size or 0) > MAX_FILE_MB * 1024 * 1024:
        await message.answer(f"Fayl juda katta (maksimum {MAX_FILE_MB} MB).")
        return
    content = (await bot.download(doc)).read()
    try:
        report = await import_file(session, name, content)
    except ValueError as e:
        await message.answer(f"❗ Fayl o‘qilmadi: {esc(str(e))}")
        return
    text = (
        f"📥 <b>Import yakunlandi</b>\n\n"
        f"✅ Qo‘shildi: <b>{report.added}</b>\n"
        f"⏭ Takroriy (o‘tkazib yuborildi): <b>{report.skipped_duplicates}</b>\n"
        f"❗ Xatoli qatorlar: <b>{len(report.errors)}</b>"
    )
    if report.errors:
        text += "\n\n" + "\n".join(esc(e) for e in report.errors[:15])
        if len(report.errors) > 15:
            text += f"\n... va yana {len(report.errors) - 15} ta"
    await message.answer(text)
