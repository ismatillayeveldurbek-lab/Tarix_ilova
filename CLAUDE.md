# Tarix — Telegram Mini App (loyiha konteksti)

Bu fayl Claude Code uchun. Har sessiya boshida o'qiladi. Muloqot va UI matnlari — o'zbek tilida (lotin).

## Maqsad
Milliy sertifikat imtihoniga tarix fanidan tayyorlovchi Telegram Mini App. Namuna — mezonapp.uz.
Batafsil tahlil: `docs/mezon-tahlili.md` (dizayn tizimi, ekranlar, 13 o'yin, gamifikatsiya,
animatsiyalar, API, Mezonning kamchiliklari). Yangi funksiyani qilishdan oldin shu hujjatning
tegishli bo'limini o'qi.

## Asosiy tamoyillar
1. Kontent — poydevor. Hamma narsa (kartochka, test, o'yin) bitta faktlar bazasidan tuziladi.
   Har fakt darslik, sinf va betga bog'langan; foydalanuvchiga doim manba ko'rsatiladi.
2. Javob to'g'riligi, ochko, XP, limitlar va taymer SERVERDA hisoblanadi. Klient faqat ko'rsatadi.
3. Har xato avtomatik takrorlashga (SRS) tushadi.
4. Avval kichik, ishlaydigan versiya; keyin kengaytirish.

## Faktlar bazasi
- Fayl(lar): `data/` papkasida (CSV, UTF-8). Ustunlar: id, tur, nom, matn, sana_matn, yil_boshi,
  yil_oxiri, asr, davr, hudud, sinf, kitob_id, paragraf, mavzu_nomi, bet, iqtibos,
  shaxs_faoliyati, shaxs_ishoralar, urush_tomonlari, golib, natija, joy_turi, joy_hozirgi,
  asar_muallifi, ishonch, izoh.
- `tur`: sana | shaxs | atama | joy | urush | asar. Mil. avv. yillar manfiy son.
- Ko'p qiymatli maydonlar " || " bilan ajratilgan.
- Import skripti `ishonch=past` qatorlarni alohida belgilasin va foydalanuvchiga ko'rsatmasin.
- Agar haqiqiy CSV ustunlari bu ro'yxatdan farq qilsa — CSV'ga moslash va bu faylni yangilash.

## Texnologiya (tavsiya; foydalanuvchi hali yakuniy tasdiqlamagan — o'zgartirishdan oldin so'ra)
- Backend: Python 3.12, FastAPI, SQLAlchemy + Alembic, PostgreSQL
- Frontend: React + Vite + TypeScript, Tailwind CSS, Telegram Mini App SDK
  (TASDIQLANGAN: Tailwind CSS v4 — 2-bosqichdan. Yangi ekranlar Tailwind'da; eski ekranlar
  `webapp/src/styles.css` (legacy qatlami) da, bosqichma-bosqich ko'chiriladi)
- Bot: aiogram 3 (faqat /start va "Ochish" tugmasi, keyin eslatmalar)
- Auth: Telegram WebApp initData'ni serverda HMAC bilan tekshirish; sessiya — httpOnly cookie
- Hosting (boshlanishiga): Vercel (frontend), Railway yoki Render (backend), Supabase yoki
  Railway PostgreSQL
- Maxfiy qiymatlar (BOT_TOKEN, DATABASE_URL) faqat `.env` da; `.env` git'ga qo'shilmaydi,
  `.env.example` saqlanadi.

## MVP bosqichlari (shu tartibda)
1. Backend poydevori: DB sxemasi (books, facts, users, user_fact_state, daily_stats),
   CSV import skripti, initData auth, `/api/v1/me`.
2. Mini App qobig'i: pastki navigatsiya (Bosh, Mashq, Profil), dizayn tokenlari
   (`docs/mezon-tahlili.md` → "Dizayn tizimi"), Telegram safe-area.
3. Kunlik takrorlash (SRS): kartochka → "Javobni ko'rish" → "Bildim / Bilmadim".
   Holatlar: yangi, o'rganilmoqda, takrorlash_kerak, o'zlashtirildi. "Bilmadim" — 10 daqiqa,
   "Bildim" — interval oshib boradi (1, 4, 10, 25 kun...).
4. O'yin "Qaysi biri oldin?": server sessiyasi (start → act → finish), 60 soniya, juftliklar
   oralig'i asta torayadi, javobdan keyin ikkala yil va darslik beti.
5. XP, kunlik seriya, kunlik limitlar (Toshkent vaqti 00:00 da yangilanadi).
6. 20–30 o'quvchi bilan sinov. Liga, mock, to'lov — keyingi bosqich.

## Mezon xatolarini takrorlamaslik (kontent validatsiyasi)
- Manba (bet) aynan shu faktga tegishli bo'lsin; o'yin ichida va natijada bir xil manba.
- Ikki voqea bitta sanaga qo'shilmasin; kontekstsiz gaplar ("Bu hududda...") ishlatilmasin.
- Chalg'ituvchi variantlar o'sha davr va turdan bo'lsin, bema'ni bo'lmasin.
- Atama ta'rifi atamaning o'zini o'z ichiga olmasin.
- Yopiq kartalar/javoblar klientga oldindan yuborilmasin.
- Vaqt/sana so'raladigan savol va o'yinlarda ("Qaysi biri oldin?", "Qachon?") javobdan OLDIN
  darslik, sinf va davr ko'rsatilmasin va klientga yuborilmasin — sinf davrni bildiradi (6-sinf —
  qadimgi, 11-sinf — eng yangi) va javobni aytib qo'yadi. Manba javobdan keyin ko'rsatiladi.
- Qo'shtirnoqlar ikki marta qo'yilmasin; o‘ va g‘ uchun ‘ belgisi.

## Ish uslubi
- Har bosqichni kichik qadamlarga bo'l, avval reja ko'rsat, keyin kod yoz.
- Har qadamdan keyin ishga tushirib tekshir (testlar yoki qo'lda) va qisqa xulosa ber.
- Foydalanuvchi dasturchi bo'lmasligi mumkin: buyruqlarni aniq ko'rsat, nima qilishini tushuntir.
