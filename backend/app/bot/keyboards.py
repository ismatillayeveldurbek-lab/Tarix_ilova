"""Bot tugmalari."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from app.bot.texts import t
from app.services.translit import tr


def alphabet_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Lotin", callback_data="alph:latn"),
        InlineKeyboardButton(text="Кирилл", callback_data="alph:cyrl"),
    ]])


def main_menu(a: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text=t("btn_quiz", a)), KeyboardButton(text=t("btn_review", a))],
            [KeyboardButton(text=t("btn_exam", a)), KeyboardButton(text=t("btn_rating", a))],
            [KeyboardButton(text=t("btn_profile", a)), KeyboardButton(text=t("btn_settings", a))],
        ],
    )


def quiz_mode_kb(a: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("mode_mixed", a), callback_data="qm:mixed")],
        [InlineKeyboardButton(text=t("mode_period", a), callback_data="qm:period")],
        [InlineKeyboardButton(text=t("mode_topic", a), callback_data="qm:topic")],
    ])


def list_kb(items: list[tuple[str, str]], a: str) -> InlineKeyboardMarkup:
    """items: [(matn, callback_data), ...] — har biri alohida qatorda."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=tr(text, a), callback_data=data)] for text, data in items
    ])


def answer_kb(question_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=letter.upper(), callback_data=f"ans:{question_id}:{letter}")
        for letter in "abcd"
    ]])


def after_answer_kb(question_id: int, a: str, last: bool) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_finish" if last else "btn_next", a), callback_data="nxt")],
        [InlineKeyboardButton(text=t("btn_report", a), callback_data=f"rep:{question_id}")],
    ])


def report_only_kb(question_id: int, a: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_report", a), callback_data=f"rep:{question_id}")],
    ])


def continue_kb(a: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_continue", a), callback_data="nxt")],
    ])


def settings_kb(a: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_switch_alphabet", a), callback_data="set:alphabet")],
        [InlineKeyboardButton(text=t("btn_toggle_reminder", a), callback_data="set:reminder")],
    ])


def report_admin_kb(report_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Tuzatildi", callback_data=f"rs:fixed:{report_id}"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"rs:rejected:{report_id}"),
    ], [
        InlineKeyboardButton(text="🚫 Savolni o'chirish", callback_data=f"rs:off:{report_id}"),
    ]])
