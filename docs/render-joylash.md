# Ilovani Render'ga joylash (tekin)

Natija: bot, Mini App va admin panel `https://tarix-....onrender.com` manzilida ishlaydi.
Uchta tekin xizmat kerak:

| Xizmat | Vazifasi |
|---|---|
| **Neon** (neon.tech) | Ma’lumotlar bazasi (PostgreSQL) |
| **Render** (render.com) | Ilovaning o‘zi: bot + Mini App + admin panel |
| **UptimeRobot** (uptimerobot.com) | Har 5 daqiqada ilovani "turtib", uxlab qolishiga yo‘l qo‘ymaydi |

Taxminan 20–30 daqiqa vaqt oladi. Bank kartasi kerak emas.

> Maxfiy qiymatlarni (bot tokeni, baza manzili) **hech kimga yubormang va chatga yozmang**.
> Ular faqat Render sozlamalariga kiritiladi.

---

## 0. Kodni `main` branchga birlashtirish

GitHub'da repozitoriy → **Pull requests** → PR #1 → **Ready for review** → **Merge pull request**.
Render `main` branchdagi kodni oladi va har yangi o‘zgarishda o‘zi qayta joylaydi.

## 1. Bot tokeni va admin ID

1. Telegram'da **@BotFather** → `/newbot` (bot bo‘lsa `/mybots` → bot → **API Token**).
   Tokenni nusxalab qo‘ying: `123456789:AA...` ko‘rinishida.
2. **@userinfobot** ga yozing — u sizning **ID** raqamingizni beradi (masalan `5012345678`).
   Bu admin ID: `/panel` buyrug‘i faqat shu odamga ishlaydi.

## 2. Neon: ma’lumotlar bazasi

1. https://neon.tech → **Sign up** (GitHub bilan kirish qulay).
2. **Create project**: nom — `tarix`, Postgres versiyasi — 16 yoki yangisi,
   region — **AWS Europe Central (Frankfurt)**.
3. Loyiha ochilgach **Connect** tugmasi → ulanish manzilini nusxalang. U shunday ko‘rinadi:
   ```
   postgresql://neondb_owner:parol@ep-....eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
   ```
   Manzilni o‘zgartirmasdan oling. Ilova uni o‘zi moslaydi.

## 3. Render: ilovani joylash

1. https://render.com → **Get Started** → **GitHub** bilan kiring va Render'ga
   `Tarix_ilova` repozitoriyasiga ruxsat bering.
2. **New +** → **Blueprint** → `Tarix_ilova` repozitoriyasini tanlang.
   Render `render.yaml` faylini o‘qiydi va `tarix` nomli xizmatni ko‘rsatadi (Free tarif).
3. Render maxfiy qiymatlarni so‘raydi:

   | Nomi | Nima yoziladi |
   |---|---|
   | `BOT_TOKEN` | 1-qadamdagi bot tokeni |
   | `DATABASE_URL` | 2-qadamdagi Neon manzili |
   | `ADMIN_IDS` | sizning ID raqamingiz (bir nechta bo‘lsa vergul bilan: `111,222`) |
   | `CHANNEL_ID` | "Tarixda bugun" kanali, masalan `@mening_kanalim` (kerak bo‘lmasa bo‘sh) |

   Kanalga post chiqishi uchun botni kanalga **admin** qilib qo‘shing.
4. **Apply** (yoki **Deploy Blueprint**). Birinchi joylash 5–10 daqiqa davom etadi:
   Mini App yig‘iladi, bazada jadvallar yaratiladi, 3987 ta fakt yuklanadi.
5. Xizmat sahifasida yashil **Live** yozuvi chiqqach, yuqoridagi manzilni
   (`https://tarix-xxxx.onrender.com`) oching va oxiriga `/api/health` qo‘shing.
   `{"ok":true}` chiqsa, ilova ishlayapti.

`WEBAPP_URL` ni yozish shart emas: ilova Render manzilini o‘zi oladi va botning
"📱 Ilova" menyu tugmasini shu manzilga sozlaydi.

## 4. UptimeRobot: uxlab qolmasligi uchun

Render'ning tekin serveri 15 daqiqa hech kim kirmasa uxlaydi. Uxlagan bot xabarlarga
javob bermaydi va 19:00 eslatmalari ketmaydi. Buni oldini olish uchun:

1. https://uptimerobot.com → ro‘yxatdan o‘ting.
2. **New monitor** → turi **HTTP(s)**, URL: `https://tarix-xxxx.onrender.com/api/health`,
   interval: **5 minutes** → **Create**.

Bitta doim yoqiq xizmat oyiga ~744 soat ishlaydi. Render bergan tekin 750 soatga sig‘adi,
lekin shu akkauntda boshqa tekin xizmat ochmang.

## 5. Tekshirish

1. Botga `/start` yozing → **📱 Ilova** tugmasi orqali Mini App ochilsin.
2. Kartochka yeching, "Qaysi biri oldin?" o‘ynang, Profilda XP ko‘rinsin.
3. Botga `/panel` yozing → admin panel havolasi kelsin (faqat `ADMIN_IDS` dagilarga).

---

## Ilova sekin ishlasa

| Sabab | Belgisi | Yechim |
|---|---|---|
| **Server uxlab qolgan** | Birinchi ochilish 30–60 soniya, keyin tez | UptimeRobot monitorini yoqing (4-qadam) |
| **Render va Neon turli mintaqada** | Har bir sahifa doim 2–5 soniya | Ikkalasi ham **Frankfurt** bo‘lishi kerak (pastda) |
| **Neon bazasi uxlagan** | Uzoq tanaffusdan keyingi birinchi amal 1–2 soniya | Tekin tarifda normal holat |

**Mintaqani tekshirish:**
- Render → xizmat → **Settings** → **Region**. Bu yerda **Frankfurt (EU Central)** turishi kerak.
- Neon → loyiha → **Settings** → **Region**. Bu yerda **AWS Europe Central 1 (Frankfurt)** turishi kerak.

Mintaqani keyin o‘zgartirib bo‘lmaydi. Render boshqa mintaqada bo‘lsa (masalan, Oregon), yangi Web Service oching va region sifatida Frankfurt'ni tanlang. Environment qiymatlarini (`BOT_TOKEN`, `DATABASE_URL`, `ADMIN_IDS`) qayta kiriting, keyin eski xizmatni o‘chiring. Ma’lumotlar Neon'da, shuning uchun hech narsa yo‘qolmaydi.
Frankfurt O‘zbekistonga ham yaqin: telefondan serverga har bir so‘rov Amerikadagidan taxminan 3 baravar tez boradi.

## Ko‘p uchraydigan muammolar

| Belgisi | Sabab va yechim |
|---|---|
| Joylash **Failed**, logda `DATABASE_URL` xatosi | Neon manzili to‘liq nusxalanmagan. Render → xizmat → **Environment** → qayta yozing → **Save, rebuild and deploy** |
| Logda `Unauthorized` | Bot tokeni noto‘g‘ri. BotFather'dan qayta oling |
| Bot javob bermaydi, sayt birinchi ochilishi 30–50 soniya | Server uxlagan. UptimeRobot monitori ishlayotganini tekshiring |
| Logda `Conflict: terminated by other getUpdates` | Bot boshqa joyda ham ishlayapti (masalan kompyuteringizda). U yerda to‘xtating. Yangi versiya joylanayotganda bir-ikki daqiqa chiqishi normal |
| `/panel` "ruxsat yo‘q" deydi | `ADMIN_IDS` da ID'ngiz to‘g‘ri yozilganini tekshiring |

**Loglar:** Render → xizmat → **Logs**. Xatoni ko‘rsangiz, logdan parchani nusxalab yuboring
(token yoki parol ko‘rinib qolsa, o‘chirib tashlang).

**Ma’lumotlar xavfsizligi:** hamma ma’lumot (foydalanuvchilar, javoblar, rasmlar) Neon bazasida.
Render serveri qayta ishga tushsa ham hech narsa yo‘qolmaydi.
Baza nusxasi uchun Neon → **Backup & Restore**.

## Tekin tarif chegaralari (o‘zgarishi mumkin)

- **Render Free:** 512 MB xotira, oyiga 750 soat, jim tursa uxlaydi.
- **Neon Free:** 0,5 GB joy, oylik hisoblash soatlari cheklangan. Baza jim turganda uxlaydi.
  Shuning uchun eslatma vazifasi bazani faqat kimdir tanlagan daqiqada tekshiradi.
- 20–30 o‘quvchi uchun bu yetarli. Foydalanuvchilar ko‘paysa, Render **Starter** tarifiga
  o‘tish kerak bo‘ladi (oyiga ~7$): server uxlamaydi va UptimeRobot kerak bo‘lmaydi.
