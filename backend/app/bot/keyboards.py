"""Bot tugmalari."""
from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo,
)

from app.bot.texts import t
from app.config import settings


def webapp(path: str = "") -> WebAppInfo | None:
    """Mini App manzili. path — ilova ichidagi sahifa, masalan "exam"."""
    if not settings.webapp_url:
        return None
    return WebAppInfo(url=settings.webapp_url.rstrip("/") + "/" + (f"#/{path}" if path else ""))


def main_menu() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=t("btn_daily")), KeyboardButton(text=t("btn_quiz"))],
        [KeyboardButton(text=t("btn_review")), KeyboardButton(text=t("btn_exam"))],
        [KeyboardButton(text=t("btn_rating")), KeyboardButton(text=t("btn_profile"))],
        [KeyboardButton(text=t("btn_settings"))],
    ]
    if settings.webapp_url:
        rows[-1].append(KeyboardButton(text=t("btn_app"), web_app=webapp()))
    return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=rows)


def webapp_button_kb(text: str, path: str = "") -> InlineKeyboardMarkup | None:
    info = webapp(path)
    if info is None:
        return None
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=text, web_app=info)]])


def reminder_kb() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=t("btn_start_daily"), callback_data="daily:start")]]
    if settings.webapp_url:
        rows.append([InlineKeyboardButton(text=t("btn_app"), web_app=webapp())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def quiz_mode_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("mode_mixed"), callback_data="qm:mixed")],
        [InlineKeyboardButton(text=t("mode_period"), callback_data="qm:period")],
        [InlineKeyboardButton(text=t("mode_topic"), callback_data="qm:topic")],
    ])


def list_kb(items: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    """items: [(matn, callback_data), ...] — har biri alohida qatorda."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data=data)] for text, data in items
    ])


def answer_kb(question_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=letter.upper(), callback_data=f"ans:{question_id}:{letter}")
        for letter in "abcd"
    ]])


def after_answer_kb(question_id: int, last: bool) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_finish" if last else "btn_next"), callback_data="nxt")],
        [InlineKeyboardButton(text=t("btn_report"), callback_data=f"rep:{question_id}")],
    ])


def report_only_kb(question_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_report"), callback_data=f"rep:{question_id}")],
    ])


def continue_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_continue"), callback_data="nxt")],
    ])


def settings_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_toggle_reminder"), callback_data="set:reminder")],
    ])


def report_admin_kb(report_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Tuzatildi", callback_data=f"rs:fixed:{report_id}"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"rs:rejected:{report_id}"),
    ], [
        InlineKeyboardButton(text="🚫 Savolni o'chirish", callback_data=f"rs:off:{report_id}"),
    ]])
