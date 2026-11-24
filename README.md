# Tarix — milliy sertifikatga tayyorgarlik boti 📜

Telegram bot va Mini App: tarix fanidan milliy sertifikat imtihoniga tayyorlanuvchilar uchun.
Interfeys o'zbek tilida, lotin va kirill alifbolari bilan.

## Bosqichlar

| # | Bosqich | Holat |
|---|---|---|
| 1 | Bot ishga tushadi: `/start`, alifbo tanlash, menyu, baza | ✅ |
| 2 | Test oqimi: savol → javob → izoh, "Xato bor" tugmasi, CSV/Excel import, admin | ✅ |
| 3 | Xatolar ustida ishlash (spaced repetition), streak, kunlik eslatma 19:00 | ⏳ |
| 4 | Sinov imtihoni (taymer, ball, daraja), haftalik reyting, "Tarixda bugun" (kanal + bot) | ⏳ |
| 5 | Mini App (FastAPI + React), hosting | ⏳ |

---

## Kompyuteringizda ishga tushirish (qadam-baqadam)

### 0. Kerakli dasturlar
- **Python 3.12 yoki yangiroq**: https://www.python.org/downloads/
  (Windows'da o'rnatishda **"Add Python to PATH"** belgisini qo'ying.)
- **Git**: https://git-scm.com/

Tekshirish uchun terminalda (Windows'da PowerShell) quyidagilarni yozing:
```bash
python --version
git --version
```

### 1. Bot tokenini olish
1. Telegramda **@BotFather** ni oching va `/newbot` yozing.
2. Botga nom bering (masalan, `Tarix Sertifikat`), so'ng username bering (oxiri `bot` bilan tugashi kerak).
3. BotFather sizga `123456789:AAH...` ko'rinishidagi **token** beradi.
   ⚠️ Tokenni hech kimga ko'rsatmang va kodga yozmang. U faqat `.env` faylida saqlanadi.
4. O'z Telegram ID raqamingizni bilish uchun **@userinfobot** ga yozing. Bu raqam sizni admin qiladi.

### 2. Loyihani yuklab olish
```bash
git clone https://github.com/ismatillayeveldurbek-lab/Tarix_ilova.git
cd Tarix_ilova/backend
```

### 3. Virtual muhit (loyiha kutubxonalari uchun alohida "quti")
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
```
Muhit faol bo'lsa, terminal qatori boshida `(.venv)` yozuvi chiqadi.
Har safar yangi terminal ochganingizda `activate` buyrug'ini qayta yozing.

### 4. `.env` faylini yaratish
`backend/.env.example` faylidan nusxa olib, nomini `.env` qiling:
```bash
# Windows:
copy .env.example .env
# macOS / Linux:
cp .env.example .env
```
`.env` faylini istalgan matn muharririda oching va to'ldiring:
```
BOT_TOKEN=BotFather bergan token
ADMIN_IDS=sizning Telegram ID raqamingiz
```
`.env` fayli `.gitignore` ichida ko'rsatilgan, shuning uchun GitHub'ga **yuklanmaydi**.

### 5. Bazani yaratish va namuna savollarni yuklash
```bash
alembic upgrade head      # jadvallarni yaratadi (tarix.db fayli paydo bo'ladi)
python -m scripts.seed    # 20 ta savol, "Tarixda bugun" voqealari, imtihon formati
```

### 6. Botni ishga tushirish
```bash
python -m app.bot.main
```
Terminalda `Bot ishga tushdi: @sizning_botingiz` chiqadi. Telegramda botingizni ochib, `/start` bosing.
Botni to'xtatish uchun terminalda `Ctrl + C` bosing.

### 7. Testlarni ishga tushirish (ixtiyoriy)
```bash
pytest
```
Testlar botni Telegramga ulanmasdan sinaydi: o'girish, import, takrorlash tizimi va to'liq test oqimi.

---

## Bot imkoniyatlari (hozircha)

**Foydalanuvchi uchun:**
- `/start` buyrug'i va alifbo tanlash (lotin / kirill). Keyin `/alifbo` yoki ⚙️ Sozlamalar orqali almashtirish mumkin.
- 📝 **Test ishlash**: aralash, davr bo'yicha yoki mavzu bo'yicha, har safar 10 ta savol.
- Har javobdan keyin ✅/❌ belgisi, to'g'ri javob va 💡 izoh ko'rsatiladi.
- ⚠️ **Xato bor** tugmasi savoldagi xatoni adminga yuboradi.
- 👤 **Profil**: statistika, streak va takrorlash kutayotgan savollar soni.

**Admin uchun** (`ADMIN_IDS` da ko'rsatilgan ID egalari):
- `/admin` — statistika va buyruqlar ro'yxati
- `/reports` — yangi xato xabarlari, har birida tugmalar bor: ✅ Tuzatildi / ❌ Rad etish / 🚫 Savolni o'chirish
- `/shablon` — import uchun namuna CSV fayl
- 📎 **.xlsx yoki .csv faylni botga yuborsangiz**, savollar import qilinadi

### Savollar fayli formati

| savol | a | b | c | d | togri | izoh | mavzu | davr | qiyinlik |
|---|---|---|---|---|---|---|---|---|---|
| Amir Temur qaysi yilda tug'ilgan? | 1320 | 1336 | 1370 | 1405 | B | 1336-yil 9-aprelda... | Amir Temur va Temuriylar | O'rta asrlar | 1 |

- `togri` ustuniga A, B, C yoki D yoziladi.
- `qiyinlik` ustuniga 1, 2, 3 yoki `oson`, `o'rta`, `qiyin` yoziladi. Bo'sh qolsa, 1 deb olinadi.
- Bazada yo'q mavzu yoki davr avtomatik yaratiladi.
- Matni bir xil bo'lgan savol qayta qo'shilmaydi.
- CSV faylda vergul (`,`) ham, nuqta-vergul (`;`) ham ishlaydi. Fayl UTF-8 kodlashda bo'lishi kerak.
- **Savollar faqat lotinda yoziladi**, kirill varianti avtomatik hosil bo'ladi.

---

## Loyiha tuzilmasi

```
backend/
├── .env.example          # sozlamalar namunasi
├── requirements.txt      # Python kutubxonalari
├── alembic/              # baza migratsiyalari (jadval o'zgarishlari tarixi)
├── app/
│   ├── config.py         # .env'ni o'qiydi
│   ├── db.py             # bazaga ulanish
│   ├── models/           # jadvallar
│   ├── services/         # biznes logika (bot ham, Mini App ham shundan foydalanadi)
│   │   ├── translit.py   #   lotin → kirill
│   │   ├── quiz.py       #   savol tanlash, javobni qayd etish
│   │   ├── review.py     #   Leitner qutilari (spaced repetition)
│   │   ├── streak.py     #   kunlik streak
│   │   └── importer.py   #   Excel/CSV import
│   └── bot/
│       ├── main.py       # botni ishga tushirish
│       ├── texts.py      # BARCHA matnlar shu yerda
│       ├── keyboards.py  # tugmalar
│       ├── middlewares.py
│       └── handlers/     # start, quiz, report, settings, admin, menu
├── data/                 # namuna savollar va "Tarixda bugun" voqealari
├── scripts/seed.py       # namuna ma'lumotlarni yuklash
└── tests/                # avtomatik testlar
```

## Asosiy g'oyalar

- **Matnlar faqat lotinda saqlanadi.** Kirill tanlagan foydalanuvchiga `translit.py` ko'rsatish paytida o'giradi, shuning uchun har bir savolni ikki marta yozish kerak emas.
- **Xatolar ustida ishlash (Leitner tizimi).** Xato javob berilgan savol 0-qutiga tushadi va ertaga qayta beriladi. Har to'g'ri javobda keyingi qutiga o'tadi: oraliqlar 1 → 2 → 4 → 7 → 15 → 30 kun. Oxirgi qutidan o'tgan savol "o'zlashtirildi" deb belgilanadi.
- **Imtihon formati sozlanadi.** `exam_configs` jadvalida JSON ko'rinishida saqlanadi: qaysi qiyinlikdan nechta savol, har birining bali va daraja chegaralari. Rasmiy spetsifikatsiya chiqqanda kodni emas, faqat sozlamani o'zgartirasiz.
- **Kelajakka tayyor.** `users` jadvalida `premium_until` (Click/Payme obunasi) va `referred_by` (referal) maydonlari bor. Mavzular bo'yicha o'zlashtirish foizi `answers` jadvalidan hisoblanadi.

## PostgreSQL'ga o'tish (serverda)
`.env` faylida bazaning manzilini o'zgartirish kifoya:
```
DATABASE_URL=postgresql+asyncpg://user:parol@host:5432/tarix
```
So'ng `alembic upgrade head` va `python -m scripts.seed` buyruqlarini ishga tushiring.
