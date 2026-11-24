"""Botning barcha matnlari shu yerda, LOTIN yozuvida.

Kirill tanlagan foydalanuvchiga `t()` funksiyasi avtomatik o'giradi.
Matnni o'zgartirmoqchi bo'lsangiz, faqat shu faylni tahrirlang.
"""
from app.services.translit import tr

TEXTS: dict[str, str] = {
    # Boshlash
    "choose_alphabet": "Assalomu alaykum! Alifboni tanlang:\nАссалому алайкум! Алифбони танланг:",
    "welcome": (
        "<b>Tarix — milliy sertifikatga tayyorgarlik</b> 📜\n\n"
        "Bu yerda siz:\n"
        "• mavzu va davrlar bo'yicha test ishlaysiz;\n"
        "• har javobdan keyin izoh o'qiysiz;\n"
        "• xatolaringiz ustida ishlaysiz;\n"
        "• sinov imtihonini topshirasiz.\n\n"
        "Quyidagi menyudan boshlang 👇"
    ),
    "alphabet_saved": "✅ Alifbo saqlandi.",

    # Menyu tugmalari
    "btn_quiz": "📝 Test ishlash",
    "btn_review": "🔁 Xatolar ustida ishlash",
    "btn_exam": "🎯 Sinov imtihoni",
    "btn_rating": "🏆 Reyting",
    "btn_profile": "👤 Profil",
    "btn_settings": "⚙️ Sozlamalar",
    "coming_soon": "🔜 Bu bo'lim keyingi bosqichda qo'shiladi.",

    # Test
    "choose_mode": "Qanday test ishlaysiz?",
    "mode_mixed": "🎲 Aralash",
    "mode_period": "📜 Davr bo'yicha",
    "mode_topic": "📚 Mavzu bo'yicha",
    "choose_period": "Davrni tanlang:",
    "choose_period_for_topic": "Avval davrni tanlang:",
    "choose_topic": "Mavzuni tanlang:",
    "no_questions": "😕 Bu bo'limda hozircha savol yo'q.",
    "question_header": "<b>Savol {n}/{total}</b>",
    "correct": "✅ <b>To'g'ri!</b>",
    "wrong": "❌ <b>Noto'g'ri.</b> To'g'ri javob: <b>{letter}) {answer}</b>",
    "your_answer": "Sizning javobingiz: {letter}",
    "explanation": "💡 <b>Izoh:</b> {text}",
    "btn_next": "Keyingi ➡️",
    "btn_finish": "Yakunlash 🏁",
    "btn_report": "⚠️ Xato bor",
    "quiz_expired": "Bu test yakunlangan yoki eskirgan. Yangisini boshlang: 📝 Test ishlash",
    "quiz_done": (
        "🏁 <b>Test yakunlandi!</b>\n\n"
        "Natija: <b>{correct}/{total}</b> ({percent}%)\n"
        "🔥 Streak: <b>{streak}</b> kun"
    ),
    "quiz_done_review_hint": "\n\nXato javoblar \"🔁 Xatolar ustida ishlash\" bo'limiga qo'shildi.",
    "streak_up": "🔥 Streak: {streak} kun!",

    # Xato xabari
    "report_ask": "Savoldagi xatoni qisqacha yozing (masalan: \"to'g'ri javob B emas, C\").\nBekor qilish: /bekor",
    "report_thanks": "🙏 Rahmat! Xabaringiz adminlarga yuborildi.",
    "report_cancelled": "Bekor qilindi.",
    "btn_continue": "Davom etish ➡️",

    # Sozlamalar
    "settings": (
        "⚙️ <b>Sozlamalar</b>\n\n"
        "Alifbo: <b>{alph}</b>\n"
        "Kunlik eslatma: <b>{reminder}</b>"
    ),
    "on": "yoqilgan ({time})",
    "off": "o'chirilgan",
    "btn_switch_alphabet": "🔤 Alifboni almashtirish",
    "btn_toggle_reminder": "🔔 Eslatmani yoqish/o'chirish",

    # Profil
    "profile": (
        "👤 <b>Profil</b>\n\n"
        "Jami javoblar: <b>{total}</b>\n"
        "To'g'ri javoblar: <b>{correct}</b> ({percent}%)\n"
        "🔥 Streak: <b>{streak}</b> kun (eng yaxshi: {best})\n"
        "🔁 Takrorlash kutayotgan savollar: <b>{due}</b>"
    ),
}


def t(key: str, alphabet: str = "latn", **kwargs) -> str:
    """Matnni alifboga o'giradi, so'ng {o'zgaruvchilarni} qo'yadi.

    Diqqat: kwargs qiymatlari o'girilmaydi (masalan, A/B/C/D harflari lotinda qolishi kerak).
    Savol matni kabi dinamik qiymatlarni chaqiruvchi o'zi `tr()` orqali o'giradi.
    """
    text = tr(TEXTS[key], alphabet)
    return text.format(**kwargs) if kwargs else text


def both(key: str) -> set[str]:
    """Tugma matnining ikkala alifbodagi ko'rinishi (filtrlar uchun)."""
    return {t(key, "latn"), t(key, "cyrl")}
