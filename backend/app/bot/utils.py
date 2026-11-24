import html

from aiogram.fsm.context import FSMContext

from app.bot.texts import both


def esc(text: str) -> str:
    """Foydalanuvchi/baza matnini HTML uchun xavfsiz qiladi."""
    return html.escape(text or "", quote=False)


MENU_KEYS = ("btn_quiz", "btn_review", "btn_exam", "btn_rating", "btn_profile", "btn_settings")
MENU_TEXTS: set[str] = set().union(*(both(k) for k in MENU_KEYS))


async def leave_input_state(state: FSMContext) -> None:
    """Menyu bosilganda kutilayotgan kiritishni (masalan, xato xabari) bekor qiladi."""
    if await state.get_state() is not None:
        await state.set_state(None)
