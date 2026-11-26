"""Botning barcha matnlari shu yerda.

Matnni o‘zgartirmoqchi bo‘lsangiz, faqat shu faylni tahrirlang.
"""

TEXTS: dict[str, str] = {
    # Boshlash
    "welcome": (
        "<b>Tarix — milliy sertifikatga tayyorgarlik</b> 📜\n\n"
        "Bu yerda siz:\n"
        "• mavzu va davrlar bo‘yicha test ishlaysiz;\n"
        "• har javobdan keyin izoh o‘qiysiz;\n"
        "• xatolaringiz ustida ishlaysiz;\n"
        "• sinov imtihonini topshirasiz.\n\n"
        "Quyidagi menyudan boshlang 👇"
    ),

    # Menyu tugmalari
    "btn_quiz": "📝 Test ishlash",
    "btn_review": "🔁 Xatolar ustida ishlash",
    "btn_exam": "🎯 Sinov imtihoni",
    "btn_rating": "🏆 Reyting",
    "btn_profile": "👤 Profil",
    "btn_settings": "⚙️ Sozlamalar",
    "btn_daily": "🔥 Kunlik 10 savol",
    "btn_app": "📱 Ilovani ochish",
    "btn_invite": "👥 Do‘stlarni taklif qilish",
    "btn_share": "📤 Do‘stga yuborish",

    # Referal
    "invite": (
        "👥 <b>Do‘stlaringizni taklif qiling!</b>\n\n"
        "Do‘stingiz havolangiz orqali botga kirib, <b>{min} ta savol</b> yechsa:\n"
        "• sizga — <b>+{xp_inviter} XP</b>\n"
        "• do‘stingizga — <b>+{xp_invited} XP</b>\n"
        "XP haftalik reytingga qo‘shiladi.\n\n"
        "Taklif qilganlar: <b>{invited}</b> · faol: <b>{active}</b> · topilgan XP: <b>{earned}</b>\n\n"
        "Sizning havolangiz:\n{link}"
    ),
    "share_text": "Tarixdan milliy sertifikatga birga tayyorlanamiz! Har kuni 10 ta savol, izohlar va sinov imtihoni 📜",
    "ref_joined": (
        "🎉 Do‘stingiz <b>{name}</b> havolangiz orqali qo‘shildi!\n"
        "U {min} ta savol yechgach, sizga <b>+{xp} XP</b> beriladi."
    ),
    "ref_activated": "🎁 <b>{name}</b> {min} ta savol yechdi — sizga <b>+{xp} XP</b> qo‘shildi!",
    "ref_welcome": "👋 Sizni do‘stingiz <b>{name}</b> taklif qildi! {min} ta savol yeching va <b>+{xp} XP</b> bonus oling.",
    "ref_bonus": "🎁 Taklif bonusi: <b>+{xp} XP</b>! Haftalik reytingga qo‘shildi.",
    "coming_soon": "🔜 Bu bo‘lim keyingi bosqichda qo‘shiladi.",

    # Test
    "choose_mode": "Qanday test ishlaysiz?",
    "mode_mixed": "🎲 Aralash",
    "mode_period": "📜 Davr bo‘yicha",
    "mode_topic": "📚 Mavzu bo‘yicha",
    "choose_period": "Davrni tanlang:",
    "choose_period_for_topic": "Avval davrni tanlang:",
    "choose_topic": "Mavzuni tanlang:",
    "no_questions": "😕 Bu bo‘limda hozircha savol yo‘q.",
    "question_header": "<b>Savol {n}/{total}</b>",
    "correct": "✅ <b>To‘g‘ri!</b>",
    "wrong": "❌ <b>Noto‘g‘ri.</b> To‘g‘ri javob: <b>{letter}) {answer}</b>",
    "your_answer": "Sizning javobingiz: {letter}",
    "explanation": "💡 <b>Izoh:</b> {text}",
    "btn_next": "Keyingi ➡️",
    "btn_finish": "Yakunlash 🏁",
    "btn_report": "⚠️ Xato bor",
    "quiz_expired": "Bu test yakunlangan yoki eskirgan. Yangisini boshlang: 📝 Test ishlash",
    "quiz_done": (
        "🏁 <b>Test yakunlandi!</b>\n\n"
        "Natija: <b>{correct}/{total}</b> ({percent}%)\n"
        "⭐ +{xp} XP\n"
        "🔥 Ketma-ket: <b>{streak}</b> kun"
    ),
    "goal_done": "🎉 <b>Kunlik maqsad bajarildi!</b> Bugun {n} ta mashq bajardingiz.\n🔥 Ketma-ket: <b>{streak}</b> kun",

    # Kunlik mashq va takrorlash
    "daily_start": "🔥 <b>Kunlik mashq</b>: {n} ta savol. Avval takrorlash vaqti kelganlar, keyin yangilari.",
    "review_start": "🔁 <b>Xatolar ustida ishlash</b>: {n} ta savol.",
    "review_empty": (
        "🎉 Hozircha takrorlash kerak bo‘lgan savol yo‘q.\n\n"
        "Xato javob bergan savollaringiz shu yerga tushadi va 1, 2, 4, 7, 15, 30 kunlik "
        "oraliqlarda qayta beriladi."
    ),
    "reminder": (
        "🔥 <b>{streak} kunlik seriyangiz bugun uzilishi mumkin!</b>\n"
        "Kunlik maqsadgacha yana <b>{n} ta mashq</b> qoldi — test, kartochka yoki o‘yin."
    ),
    "reminder_new": (
        "⏰ Bugungi <b>{n} ta mashq</b> sizni kutmoqda — test, kartochka yoki o‘yin.\n"
        "🔥 Bugun yangi seriyani boshlang: har kuni ozgina, lekin muntazam."
    ),
    "btn_start_daily": "▶️ Boshlash",

    # Imtihon
    "exam_open": (
        "🎯 <b>{name}</b>\n\n"
        "Savollar: <b>{count}</b> ta\nVaqt: <b>{minutes}</b> daqiqa\n\n"
        "Imtihon taymer bilan ilovada topshiriladi 👇"
    ),
    "btn_open_exam": "🎯 Imtihonni boshlash",
    "exam_not_configured": "Imtihon formati hali sozlanmagan.",
    "webapp_missing": "📱 Ilova (Mini App) hali sozlanmagan. Admin WEBAPP_URL ni kiritishi kerak.",

    # Reyting
    "rating_title": "🏆 <b>Haftalik reyting</b> (dushanbadan beri)",
    "rating_empty": "Bu hafta hali hech kim savol yechmadi. Birinchi bo‘ling! 💪",
    "rating_you": "Sizning o‘rningiz: <b>{place}</b> · {xp} XP",
    "rating_you_none": "Siz bu hafta hali savol yechmadingiz.",

    # Tarixda bugun
    "history_none": "📅 Bugungi sana uchun voqea kiritilmagan.",
    "quiz_done_review_hint": "\n\nXato javoblar \"🔁 Xatolar ustida ishlash\" bo‘limiga qo‘shildi.",
    "streak_up": "🔥 Ketma-ket: {streak} kun!",

    # Xato xabari
    "report_ask": "Savoldagi xatoni qisqacha yozing (masalan: \"to‘g‘ri javob B emas, C\").\nBekor qilish: /bekor",
    "report_thanks": "🙏 Rahmat! Xabaringiz adminlarga yuborildi.",
    "report_cancelled": "Bekor qilindi.",
    "report_limit": "Bugun juda ko‘p xabar yubordingiz. Ertaga urinib ko‘ring.",
    "btn_continue": "Davom etish ➡️",

    # Sozlamalar
    "settings": (
        "⚙️ <b>Sozlamalar</b>\n\n"
        "Kunlik eslatma: <b>{reminder}</b>"
    ),
    "on": "yoqilgan ({time})",
    "off": "o‘chirilgan",
    "btn_toggle_reminder": "🔔 Eslatmani yoqish/o‘chirish",

    # Profil
    "profile": (
        "👤 <b>Profil</b>\n\n"
        "Jami javoblar: <b>{total}</b>\n"
        "To‘g‘ri javoblar: <b>{correct}</b> ({percent}%)\n"
        "🔥 Ketma-ket: <b>{streak}</b> kun (rekord: {best})\n"
        "🔁 Takrorlash kutayotgan savollar: <b>{due}</b>\n"
        "📈 Umumiy o‘zlashtirish: <b>{mastery}%</b>"
    ),
    "weak_title": "\n\n⚠️ <b>Zaif mavzular</b> — mashq qilish uchun bosing:",
    "new_topic_hint": "\n\n💡 Tavsiya: <b>{name}</b> mavzusini boshlang.",
}


def t(key: str, **kwargs) -> str:
    """Matnni oladi va {o‘zgaruvchilarni} qo‘yadi."""
    return TEXTS[key].format(**kwargs) if kwargs else TEXTS[key]
