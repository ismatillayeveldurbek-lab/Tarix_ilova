# Mezon tahlili: Tarix Telegram ilovasi uchun texnik spetsifikatsiya

Nov 25, 2026 · @Eldurbek

## Xulosa

Mezon (mezonapp.uz) Milliy sertifikat imtihoniga tayyorlovchi Telegram Mini App va veb-ilova. Uning tarix moduli butunlay darsliklardan olingan faktlar bazasiga qurilgan: 9 212 fakt, 3 367 sana, 1 888 shaxs, 2 556 atama, 731 joy va 670 urush yoki shartnoma. Bundan tashqari 11 ta darslikdan 12 078 ta savol-javob tuzilgan. Har bir fakt sinf, darslik, nashr yili, mavzu va betga bog'langan.

Siz Mezon darajasidagi ilova qurmoqchi bo'lsangiz, quyidagi beshta tamoyil eng muhimi:

1. **Kontent — ilovaning poydevori.** Har bir fakt darslik betiga havola bilan saqlanadi va barcha o'yin, test, qo'llanma va takrorlash o'sha bitta bazadan avtomatik tuziladi.
2. **Bitta fakt, ko'p rejim.** Bir xil sana kartasi vaqt o'qida, "Asrlarga ajrat" o'yinida, testda va duelda ishlatiladi.
3. **Interval bilan takrorlash (SRS).** "Bildim" javobi faktni 4 kunga, "Yana ko'rsat" esa 10 daqiqaga suradi. Har kuni takrorlash navbati beriladi.
4. **Kunlik odat halqasi.** 3 ta kunlik vazifa sandiqni ochadi, "bugungi o'yin yo'li" bonus XP beradi. Bularga oylik kubok, haftalik liga va imtihongacha qolgan kunlar sanog'i qo'shiladi.
5. **Iliq, "jonli" dizayn.** Pastel osmon palitrasi, gil (clay) uslubidagi 3D illyustratsiyalar va sof CSS bilan qilingan 1 210 ta keyframe animatsiya.

Tahlil 2026-yil 25-noyabrda foydalanuvchi hisobi orqali, mobil ko'rinishda (375×812) o'tkazildi. Hisobda tanlangan fan — tarix. Ikkinchi sessiyada (o'sha kuni) barcha 13 o'yindan 11 tasi o'ynab ko'rildi, Mock, Reyting, Profil, Hamyon, Do'kon, Tariflar, Sovg'a, Taklif va Bellashuv ekranlari hamda desktop ko'rinishi o'rganildi. Ochilmagan bo'limlar oxirida ko'rsatilgan.

## Texnik arxitektura

Mezon ikki qismdan iborat: Next.js'da yozilgan frontend (mezonapp.uz) va alohida REST API (api.mezonapp.uz/api/v1). Bitta kod bazasi ham veb-sayt, ham Telegram Mini App bo'lib ishlaydi.

| Qatlam | Mezonda nima ishlatilgan | Sizga tavsiya |
| --- | --- | --- |
| Frontend | Next.js App Router, Turbopack, React Server Components (`?_rsc=` so'rovlari) | Next.js yoki Vite + React; Mini App uchun SPA ham yetadi |
| Stil | Tailwind CSS v4 va CSS Modules (har bir ekran uchun alohida modul) | Tailwind + modul CSS animatsiyalar uchun |
| Animatsiya | Faqat CSS `@keyframes` va SVG; kutubxona yo'q | Avval CSS; murakkab joylarda Motion yoki Lottie |
| Backend | Alohida API: `/api/v1/...`, xatolar `{detail:{code, message}}` ko'rinishida, xabarlar o'zbekcha | FastAPI yoki NestJS + PostgreSQL |
| Auth | Telegram Mini App initData, Telegram Login Widget, telefon + SMS OTP (6 xonali) | Mini App'da faqat `initData` tekshiruvi yetarli |
| Sessiya | httpOnly refresh cookie + xotiradagi access token (`/auth/refresh`) | Xuddi shunday: localStorage'da token saqlamang |
| To'lov | Payme (kodda), Click va Uzum (ofertada) | Payme + Click; Telegram Stars ixtiyoriy |
| Analitika | Yandex Metrika | Yandex Metrika yoki PostHog |
| Til | O'zbekcha va ruscha | Avval o'zbekcha |

**Telegram integratsiyasi.** CSS'da `--tg-safe-area-inset-*` va `--tg-content-safe-area` o'zgaruvchilari bor. Shu orqali Telegram ichidagi yuqori va pastki chegaralar hisobga olinadi. Pastki navigatsiya va toast'lar `--safe-bottom` bilan joylashtiriladi.

**Yuklanish.** Ilova avval splash ekranni ko'rsatadi: markazda logotip, fonida firuza va shaftoli rangli gradient. So'ng bosh sahifa bitta kirishda taxminan 25 ta parallel API so'rovi bilan yig'iladi (`/me`, `/me/summary`, `/me/quests`, `/league`, `/tarix/albom` va boshqalar).

**Ruxsatlar.** Kirmagan foydalanuvchi har qanday sahifadan `/kirish?next=...` sahifasiga yo'naltiriladi. Ochiq sahifalar faqat uchta: `/kirish`, `/oferta` va `/maxfiylik`. Kodda ustoz (`/ustoz`, `/sinf`, `/teacher/*`) va admin (`/admin/*`) rollari ham bor.

## Dizayn tizimi

Mezonning ko'rinishi yumshoq "osmon" palitrasi, juda yumaloq oq kartalar va gil (clay) uslubidagi 3D illyustratsiyalarga tayanadi. Natijada ilova o'quvchiga jiddiy emas, balki o'yin kabi ko'rinadi.

**Ranglar (CSS tokenlar)**

| Token | Qiymat | Qayerda ishlatiladi |
| --- | --- | --- |
| canvas | #f5f8fd | Sahifa foni |
| ink / ink-2 / ink-3 | #0f1b33 / #2c3954 / #45536e | Sarlavha va matnlar |
| muted / faint | #65728b / #8b96ab | Ikkinchi darajali matn |
| line / line-soft | #e0e7f3 / #e9eef7 | Chegaralar |
| peri (soft / mid / deep / strong) | #e4ecfb / #afc4f2 / #5c7fd1 / #2453b3 | Asosiy aksent, havolalar |
| peach / duel-me | #f2895f, #ffb592 | Iliq aksent, "men" tomoni |
| duel-op | #6f8bf0 | Raqib tomoni |
| lemon-deep | #ffe064 | Sana belgilari, sariq marker |
| success / warning / error | #3fbf7f / #f0b955 / #ff6b6f | Holatlar |
| Asosiy CTA | to'q ko'k-qora (#0f1b33 atrofida) | "Davom etish", "Boshlash" tugmalari |

Bo'limlarning har biri o'z rangiga ega: Yillar sariq, Shaxslar binafsha, Atamalar ko'k, Davlatlar firuza, Urushlar qizg'ish. Qo'llanma va o'yinlarda shu ranglar ikonka foni sifatida takrorlanadi.

**Fonlar.** Sahifa foni bir necha radial gradientdan iborat: tepada firuza, pastda shaftoli. Ustiga nuqtali to'r (`--sky-dots`) va sekin suzuvchi chiziqli geometrik shakllar qo'yilgan. Asosiy "hero" kartalar (Tarix yo'lingiz, Bugungi takrorlash) to'q ko'k gradientda, yorqin aksent bilan.

**Shriftlar.** Asosiy shrift Urbanist (100–900). Yumaloq sarlavhalar uchun Fredoka va Nunito. Matn bloklari uchun Source Serif 4, PT Serif va Noto Serif. Qo'lyozma effekti uchun Caveat. Savol matni 17px, qator oralig'i 1.55. Variantlar 16.5px.

**Shakllar.** Kartalar 20–28px radiusda, tugmalar va chiplar to'liq yumaloq (pill). Soyalar keng va yumshoq: `0 22px 36px -22px` ko'rinishida. Glass effekti uchun `bg-white/80` va `border-white/95`.

**Illyustratsiyalar.** Gil uslubidagi 3D obyektlar: kubok, sandiq, tangalar, pul, medal. Shaxslar uchun arkasimon ramkadagi portretlar ishlatiladi. Portret bo'lmasa, binafsha nuqtali doira ichida ism-familiya bosh harflari (masalan, "AB") chiqadi.

**Navigatsiya.** Pastda suzib turuvchi oq panel, beshta tab: Bosh, Mashq, Mock, Reyting, Profil. O'rtadagi "Mock" tugmasi kattaroq, firuza rangli va panel ustiga ko'tarilgan. Faol tab yumshoq firuza doira bilan belgilanadi.

## Ekranlar

Ilova o'quvchini har kuni bosh sahifaga qaytaradi. Bosh sahifa 15 ta blokdan iborat lenta: undagi har bir blok bitta keyingi harakatga olib boradi.

### Kirish (/kirish)

Yuqori yarmida illyustratsiya sahnasi bor: shohsupadagi kubok ko'targan o'quvchi qiz, bulutlar, qog'oz samolyot va suzib yuruvchi "Mezon prognozi 57,9 · B" hamda "Har javobga izoh" kartalari. Pastdan bottom sheet chiqadi. Unda "Telegram orqali kirish" (asosiy) va "Telefon raqam bilan" (ikki qadam: +998 raqam, so'ng 6 xonali SMS kod) tugmalari bor. Desktop'da sahifa ikki ustunga bo'linadi.

### Bosh sahifa (/bosh), yuqoridan pastga

1. **Salomlashish.** Avatar, "Salom, E.I!", sana va olov belgisida streak soni.
2. **Oylik kubok** ("Noyabr Kubogi"). Necha kun qolgani, foydalanuvchining ochkosi ("Faqat sizga ko'rinadi") va "Qatnashish" tugmasi.
3. **Kunlik vazifalar.** "0/3 bajarildi", qulflangan oltin sandiq ichida 45 tanga. Har vazifa uchun progress-bar, +15 tanga va "Davom etish" tugmasi. Vazifalar: 1 ta mashq (5 savol), istalgan mavzudan 8 ta to'g'ri javob, 1 ta bellashuv yoki o'yin. Ostida oylik nishon: "Noyabr: 0/20 kun".
4. **Tarix yo'lingiz** (to'q ko'k hero karta). Imtihongacha 34 kun. O'zlashtirilgan faktlar "0 / 9 212". To'rt davr bo'ylab avatar yuradigan yo'l: Qadimgi, O'rta asrlar, Yangi davr, Eng yangi. Uchta mini-statistika: takrorga faktlar, bugungi XP, reja.
5. **Bugungi reja** (1/4, 19 daqiqa). Kunlik takrorlash, bugungi o'yin yo'li (+30 XP), darslikdan § savol-javob, bo'lim bellashuvi (ixtiyoriy).
6. **Mock taymeri.** "Tarix Mock №12", yakshanba 20:00 gacha kun, soat, daqiqa va soniya sanog'i. "Qatnashaman" tugmasi, 47 qatnashchi, "Qashqadaryodan 4 kishi" (hududiy ijtimoiy isbot).
7. **Bugun tarixda.** Taqvim varag'i ko'rinishida "26-noyabr" va bir savol: "Bu qaysi yilda bo'lgan?" (3 variant).
8. **Shaxslar karuseli.** Arkasimon portretlar, ostida holat: Yangi yoki O'rganilmoqda. "Kim men?" o'yiniga havola.
9. **Qo'llanma bo'limlari.** 5 ta bo'lim, har birida jami progress va "bugun 0/80" limiti.
10. **Darsliklar.** 11 ta kitob va 349 § javon ko'rinishida (rangli kitob qirralari), "Davom" tugmasi bilan.
11. **Imtihon yo'li.** Bugun, Mock №12, Ro'yxat va Imtihon nuqtalaridan iborat vaqt o'qi. "Maqsad A+ (70 ball)", birinchi mock prognoz beradi.
12. **Sinov (trial) limitlari.** Halqa diagrammalar: Yillar 0/80, Savol-javob 4/100, Test 0/8, O'yinlar.
13. **Liga kartasi.** "Feruza ligasi": birinchi XP bilan ligaga qo'shilasiz.

### Mashq markazi (/mashq)

Yuqorida Tarix qo'llanmasi kartasi turadi. Undan keyin "Tarix savollari qo'shilmoqda" beta xabari keladi: metodistlar savollarni tekshirib, bankka qo'shmoqda. Pastda turlarga ajratilgan 12 ta o'yin ro'yxati joylashgan (Sana, Shaxs, Xarita, Atama, Aralash), har biri "0/100 XP" bilan.

### Qo'llanma (/mashq/qollanma)

Yuqorida "Yangi darslik / Eski darslik" almashtirgichi (2020–2025 va 2017–2019 nashrlari) va "Start: kunlik limitlar, Pro'da cheksiz, 59 000 so'm" banneri. Keyin "Bugungi takrorlash" hero kartasi keladi: segmentli halqada o'zlashtirish foizi va besh bo'lim chiplari. Ostida bo'limlar, savol-javob va test kartalari, tavsiya etilgan o'yinlar. Oxirida "Bugun yana bepul" ro'yxati bor: takrorlash, xaritalar va ro'yxatlarni o'qish limitga kirmaydi.

### Qo'llanma bo'limlari

| Bo'lim | Hajmi | Asosiy ko'rinish | Filtrlar va karta tuzilishi |
| --- | --- | --- | --- |
| Yillar | 3 367 sana | "Vaqt o'qi": mil. avv. CCCC asrdan XXI asrgacha gorizontal asr scrubber'i; "Ro'yxat" rejimi ham bor | Davr chiplari. Karta: sana belgisi (sariq), fakt, darslik manbasi, holat; ochilganda "Testda tekshirish" va "Bellashuvga" tugmalari |
| Shaxslar | 1 888 shaxs | 2 ustunli portret to'ri, alifbo tartibida | Tur (hukmdor, olim, shoir, sarkarda, sayyoh/elchi, davlat arbobi) va davr. Bottom sheet: portret yoki bosh harflar, teglar, "zamondoshlari" chiplari, yangi va eski darslik havolasi, "Testda tekshirish" |
| Atamalar | 2 556 atama | "Lug'at" yoki "Kartochka" rejimi | Qidiruv, davr va darslik filtrlari, o'ng tomonda A–Ch alifbo indeksi |
| Davlatlar va shaharlar | 731 nom | Sxematik SVG xarita (XVI asr va XVIII–XIX asr qatlamlari), daryolar, Ipak yo'li chizig'i; "Ro'yxat" rejimi ham bor | Shahar yoki hududni bosganda sheet ochiladi: tur, davr, tavsif, darslik beti |
| Shartnoma va urushlar | 670 voqea | Turlarga ajratilgan lenta | Janglar, urushlar, shartnomalar, qo'zg'olonlar. Karta: yil, tur, nom, "G'olib" belgisi yoki ikki tomon kartochkasi, natija, manba |

### Darslik savol-javobi

Yuqorida "Ustoz tanlovi: Imtihonda tushishi mumkin" kartasi turadi (439 savol, 12 mavzu, 4 variantli test). Undan keyin darsliklar javoni: 5–11-sinflar, O'zbekiston tarixi, Jahon tarixi va Qadimgi dunyo bo'yicha 11 ta kitob. Kitob ichida boblar va § ro'yxati, har birida savollar soni va progress. Savollar turlarga ajratilgan: Yillar, Shaxslar, Atamalar, Joylar, Voqealar, Asarlar.

Bitta § ichida ikki rejim bor:

- **Savol-javob (faol eslash).** Karta savolni ko'rsatadi va "Avval o'zingiz eslang, keyin javobni oching" deydi. "Javobni ko'rish" bosilgach karta ochiladi va "Bildingizmi?" savoli chiqadi: "Bilmadim" yoki "Bildim". Pastda nuqtali progress va "Bu safar: N bildim, M takrorlash" hisobi.
- **Test.** O'sha savol A–D variantlari bilan beriladi. To'g'ri javob yashil rangga kiradi, ✓ belgisi va halqa animatsiyasi chiqadi, qolgan variantlar xiralashadi. So'ng darslik beti va "Keyingi savol" tugmasi ko'rsatiladi. Yuqoridagi kunlik limit hisoblagichi (4/100 → 5/100) shu zahoti yangilanadi.

## O'yinlar

O'yinlar markazida 13 ta o'yin bor, ular 22 ta darslikdagi 16 658 faktdan avtomatik tuziladi. Bitta fakt bir kunda bitta o'yinda ikki marta chiqmaydi. Har o'yin kuniga 100 XP gacha beradi: 1–2-raund to'liq, 3-raund yarim, 4-raunddan boshlab XP berilmaydi (cheksiz "farm" qilishga qarshi). Kunlik umumiy chegara 300 XP.

**Bugungi o'yin yo'li.** Har kuni tizim oxirgi 7 kunda kam o'ynalgan ko'nikmalardan 3 ta o'yinni tanlaydi (bizda: Asrlarga ajrat, Kim men?, Atama yig'ish). Ular bekatlarga o'xshash nuqtalar va punktir chiziq bilan ko'rsatiladi. Uchalasi tugasa +30 XP bonus beriladi. Pastda haftalik kalendar, o'yinlar xilma-xilligi, haftalik XP va aniqlik ko'rsatiladi.

| O'yin | Tur | Mexanika | Feedback va natija (o'ynab ko'rilgan) |
| --- | --- | --- | --- |
| Asrlarga ajrat | Sana | 8 voqea, 4 asr tokchasi. Avval kartani, keyin tokchani bosasiz; tokchalar 1601–1700 kabi yil oralig'ini ko'rsatadi | Har kartaga yil belgisi chiqadi. Xato karta qizarib, animatsiya bilan to'g'ri tokchaga ko'chadi. Tokchada "2/2" hisobi. Natija sheet: 7/8, +35 XP, xatoning izohi va darslik beti, eslatma ("yilning birinchi ikki raqamiga bir qo'shing"), "Kitob izi" havolasi, "Qayta o'ynash" yoki "Keyingi o'yin" |
| Vaqt chizig'i | Sana | 5 voqeani O'rta asrlar–Yangi davr o'qidagi 5 ta joyga tartib bilan qo'yish | 5/5, +50 XP. "Keyingi raundda sanalar bir-biriga yaqinroq bo'ladi" (moslashuvchan qiyinlik). Seriya, aniqlik, ligadagi o'rin (6-o'rin) va "Sana bellashuvi"ga havola |
| Qaysi biri oldin? | Sana | 60 soniyalik blitz, 24 juftlik. Ikki voqea kartasidan oldin bo'lganini bosasiz; kartada sinf va darslik nomi bor. Oraliq 5 pog'onada torayadi: 500+, 100+, 30+, 10+ va 10 yildan kam. Ketma-ket 3 to'g'ri ochkoni x2, 6 ta x3 qiladi; xato x1 ga qaytaradi | Javobdan keyin ikkala kartada yil va "Oldin / Keyin" yorlig'i, "+10" ochko uchib chiqadi, ostida darslik beti. Natija: to'g'ri va xato, +12 XP, ochko, eng uzun seriya, aniqlik %, "Xato qilingan juftliklar" yillari bilan. Xato sanalar Yillar qo'llanmasida "Takrorlash kerak" bo'ladi. Bizda 4/8 |
| Tarix bingo | Sana | 4×4 to'rda 16 yil (4 tasi chalg'ituvchi). 12 voqea navbat bilan "aytiladi", har biriga 8 soniya. Qator, ustun yoki diagonalda 4 belgi — Bingo. Belgi +3, Bingo +8 XP | Natijada "Aytilmagan yillar ham darslikda bor" bloki: chalg'ituvchi yillar ham fakt sifatida tushuntiriladi. Topilmagan yillar takrorlashga tushadi. Bingo chizig'i SVG bilan chiziladi. Bizda 2/12, +6 XP |
| Kim men? | Shaxs | 3 ta ishora, 4 javob. Birinchi ishora bepul; har qo'shimcha ishora −10 XP (30 → 20 → 10). Portret javobdan keyin ochiladi | Karta ochilib portret yoki bosh harflar, barcha ishoralar va darslik beti chiqadi. "To'g'ri, 1 ta ishora bilan +30 XP". SRS savoli: "Qachon yana ko'rsatay?" — "Yana ko'rsat" (10 daqiqadan keyin) yoki "Bildim" (4 kundan keyin). "Eslab qolish %" va "Takrorlash N shaxs" hisobi |
| Juftlik | Shaxs | 4 rejim tabi: Shaxs — asar, Davlat — poytaxt, Atama — ma'no, Voqea — yil. 3 bosqich, har birida 4 juftlik ikki ustunda. Avval chapdan, keyin o'ngdan bosasiz | To'g'ri juftlik yashil chiziq bilan ulanadi, ostida darslik fakti va beti chiqadi. Xatoda qizil "Bu juftlik emas" kartasi, tanlov saqlanib qoladi. Bosqich oxirida medal: +10 XP yoki xatosiz bo'lsa +25 XP. Natija: 10/12, +60 XP, "Adashgan juftliklar" ("Siz «…» bilan ulagan edingiz") |
| Xarita mashqi | Xarita | 10 savol, 3 rejim: Hudud, Shahar, Yurish yo'li. Haqiqiy chegaralar (Cliopatria/Seshat va Natural Earth), zoom tugmalari, davr kesimi (masalan, mil. avv. 325-yil). Nomlar javobdan keyin ochiladi; "Bilmayman" tugmasi bor | To'g'ri: "To'g'ri, So'g'diyona — Ajoyib, davom eting", +10 XP, tarixiy izoh va darslik beti. Xato yoki "Bilmayman" bo'lsa to'g'ri hudud yashil yonadi, +0 XP. Raund oxirida oddiy panel: "1/10 to'g'ri, +10 XP", xatolar ertangi takrorlashga. Yurish yo'lida 4 ta rangli, raqamlangan marshrut |
| Kim? Qachon? Qayerda? | Xarita | 4 voqea (jang, urush, qo'zg'olon, shartnoma). Har biriga ketma-ket 3 savol: Qachon? (4 yil), Qayerda? (4 joy), Kim kimni yengdi? (4 variant). Har to'g'ri tanlov +5 XP, 6 soniyada javob bersangiz +1 tezlik bonusi | Uch qator to'lgach "muhr bosiladi" (3/3), voqea tafsiloti va bet chiqadi. Xato qatorda "1514 (siz: 1498)". Natija: 5/12, +26 XP, har voqea uchun x/3 va boshqa o'yinga tavsiya: "Eng ko'p xato: «Qachon» savollari. Qaysi biri oldin? sanalarni mustahkamlaydi" |
| Atama yig'ish | Atama | 6 atama. Ma'nosi beriladi, atamani harf plitkalaridan yig'asiz (o', g', sh, ch — bitta plitka, ortiqcha harflar ham bor). "Ishora harfi" (XP 10 → 5), "Aralash" va "O'chirish" tugmalari | Wordle'ga o'xshash: joyida bo'lmagan harflar qizarib plitkalarga qaytadi, to'g'rilari qoladi ("2 ta harf joyida emas"). To'g'ri javob: "+10 XP, 4 kundan keyin takrorlanadi"; xatodan keyin "+5 XP, ertaga takrorlanadi". Natija: 6/6, +50 XP |
| Xotira | Atama | 16 karta, 8 juft: shaxs — asar (toj belgisi) va atama — ma'no (kitob belgisi). Bir marta "Ko'rib olish" mumkin. XP yurishlar soniga bog'liq: 12 gacha +40, 16 gacha +30, 22 gacha +20, undan ko'p +10 | Karta 3D aylanadi. Xatoda "Juft emas… Joylarini eslab qoling". Topilgan juft ostida darslik fakti. Natija: 13 yurish, +30 XP, har juft necha marta ochilgani ("birinchi ochishda", "3 marta ochildi") |
| Ortiqchasini top | Aralash | 6 to'plam, har birida 4 element, bittasi begona. Belgi turi: asr, sulola, tur yoki hudud. "Ishora" belgi turini ochadi, XP 8 → 4 | Javobdan keyin "Uchalasi: …" lentasi tushadi, begona elementning izohi va beti chiqadi. Natijada belgi turlari bo'yicha to'g'ri/xato ro'yxati va "Adashgan to'plamlar". Bizda 3/6, +20 XP |
| Rost yoki yolg'on | Aralash | 60 soniya, 16 gap. Kartani o'ngga (rost) yoki chapga (yolg'on) surasiz yoki tugmani bosasiz. Yolg'on gapda bitta tafsilot almashtirilgan: yil, shaxs, poytaxt yoki lavozim. Izoh o'qilayotganda soat to'xtaydi | Har javobdan keyin "shaxs almashtirilgan" kabi yorliq va asl darslik fakti. Natija: rost va yolg'on gaplar bo'yicha alohida aniqlik, eng uzun seriya, "Eng ko'p chalg'itgani: yil almashtirilgan gaplar", adashgan gaplar asli bilan |
| Bo'lim bellashuvi | Duel | Raqib bilan 7 raund, har savolga 10 soniya. Bo'limni o'zingiz tanlaysiz (yillar, shaxslar yoki shartnomalar). Do'st yoki jonli raqib bilan. Kuniga 15 ta bepul, Pro'da cheksiz | Real raqib bilan bo'lgani uchun boshlanmadi. CSS'da arqon tortish, VS banneri, ekran silkinishi, kubok va konfetti animatsiyalari bor |

O'ynalgan o'yinlarning umumiy qolipi:

1. Yuqorida yopish (×), o'yin nomi, raund holati ("8 voqea, 1-raund, XP to'liq") va jonli XP hisoblagichi.
2. Bir qatorlik vazifa sarlavhasi va qisqa ko'rsatma.
3. O'yin maydoni. Barcha elementlar to'liq `aria-label` bilan ta'minlangan (masalan, "Nishtadt shartnomasi, XVIII asr tokchasida").
4. Pastda "Qaytadan joylash" va "Tekshirish, yana N ta" tugmalari. Tugma faqat hamma narsa joylanganda faollashadi.
5. Natija bottom sheet'i: ball, XP tafsiloti, xatolar izohi, darslikka qaytish havolasi, kunlik yo'l progressi va keyingi o'yin.

### O'yinlarning texnik qolipi (ikkinchi sessiyada aniqlandi)

Barcha 13 o'yin bitta server mexanizmiga qurilgan: klient faqat chizadi, to'g'ri javob, ochko, XP va taymer serverda hisoblanadi.

- **Sessiya.** `POST /tarix/oyin/{tur}/start` sessiya yaratadi (id, raund, boshlangan vaqt va o'yin turiga mos JSON maydon: oldin, bingo, juftlik, kqq, atama, xotira, ortiqcha, rost, xarita). Har harakat `POST /tarix/oyin/sessions/{id}/act/{pick, call, tap, pair, try, answer, begin, next}` bilan yuboriladi, oxirida `/finish`. Har so'rovda javob vaqti (`ms`) ham ketadi.
- **Server soati.** Blitz o'yinlarda `clock: {budget_ms, left_ms, running}` qaytadi. Izoh o'qilayotganda soat to'xtatiladi, shuning uchun o'quvchi feedback'ni shoshilmay o'qiydi.
- **Davom ettirish.** Sahifani yopib qaytsangiz, sessiya to'xtagan joyidan davom etadi (masalan, Xarita 2/10 dan, Kim? Qachon? Qayerda? 2/4 dan ochildi).
- **XP chegaralari.** Har o'yin kuniga 100 XP gacha, hammasi birga 300 XP. Chegara to'lgach markazda har o'yinga "Limit to'ldi" yoziladi, natija oynasida esa "Tarix o'yinlarining kunlik 300 XP limiti to'ldi".
- **Natija oynasining yagona qolipi:** ball va XP formulasi ("10 juftlik, har biri 5 XP, xatosiz bosqich +10: +60 XP"), xatolar asli va darslik beti bilan, "Kitob izi" (eng ko'p xato qilingan mavzuga havola), bugungi yo'l nuqtalari (1–2–3), "Qayta o'ynash: 2-raund XP to'liq" va "Keyingi o'yin".
- **Xatodan takrorlashga.** Har o'yindagi xato fakt qo'llanmada "Takrorlash kerak" holatiga o'tadi va ertaga birinchi chiqadi. Atama yig'ishda interval javob sifatiga qarab o'zgaradi: xatosiz — 4 kun, ishora yoki xatodan keyin — ertaga.
- **O'yinlararo tavsiya.** Natija oynasi zaif ko'nikmani nomlab, uni mashq qildiradigan boshqa o'yinni taklif qiladi.
- **Mavjudlik signali.** O'yin paytida `POST /me/pulse` (`where: oyin, busy: true`) yuboriladi: bellashuv chaqiruvlari o'yinni bo'lmasligi uchun.

**O'yinlar markazi (/oyinlar).** Yuqorida bugungi XP (300 / 300) va bugungi o'yin yo'li (har bekatda vaqt va olingan XP). Turlar bo'yicha filtr: Sana 4, Shaxs 2, Xarita 2, Atama 2, Aralash 3. Har kartada XP/100, "Limit to'ldi" yoki "Bajarildi" belgisi va oxirgi o'ynalgan vaqt. Pastda haftalik kalendar, bugungi XP o'yinlar bo'yicha taqsimoti, xilma-xillik (11 xil o'yin), hafta XP va aniqlik (51 %).

## Mock (/mock)

Mock — haqiqiy imtihon formatidagi haftalik jonli sinov, ekran uni sport tadbiri kabi taqdim etadi: sanoq taymeri, qatnashchilar soni, hududiy ijtimoiy isbot va e'londan keyingi reyting. Mock'ga yozilish va uni boshlash tugmalari bosilmadi.

- **Bosh ekran.** "Tarix Mock №12, Yakshanba, 29-noyabr, 20:00, reytingli". Kun, soat, daqiqa va soniya alohida oq kartalarda, ostida "Qatnashaman" CTA. Avatarlar qatori: "48 qatnashchi, Qashqadaryodan 4 kishi". Tartib kartasi: 150 daqiqa, 45 topshiriq, 55 element, kirish 22:00 gacha, natija e'lon qilingach.
- **"Mock qanday ishlaydi" (ⓘ tugmasi, bottom sheet).** To'rt band: Mock kuni (kirish to'xtaguncha istalgan payt boshlaysiz, yopilishda test hammaga birdan yopiladi); Natija va reyting (ball Rasch modelida, test, umumiy va o'sish reytingi); Ertasi kuni kutubxonada (qatnashmaganlar ishlay oladi, reytingsiz); Qayta ishlash (mashq hisoblanadi, prognozga kirmaydi, 14 kundan keyin ochiladi).
- **O'tgan mocklar.** Har qatorda sana pillasi, "Qatnashmagansiz", "26 kishi ishladi, o'rtacha 30,70", "Endi kutubxonada: oddiy test kabi, reytingsiz" va "Ishlash". Ostida "Namunaviy testlar": Hammasi / Yangi / Topshirilgan filtri, "Keyingi tavsiya №2 — Payshanba" va "Rejaga qo'shish".
- **Mock kuni sahifasi (/mock/kun/10).** "Natijalar e'lon qilindi" banneri, uch raqam (26 kishi, o'rtacha 30,70, eng yuqori 56,70), top-3 podium. Javoblar to'ri 1–35 va 36a–45b; u test ishlangandan keyin ochiladi. Tuzilma izohi: 1–20 siyosiy tarix, 21–26 ijtimoiy-iqtisodiy, 27–32 madaniyat, 33–35 A–F blok, 36–45 yozma javob (a va b). Ballar taqsimoti gistogrammasi (mediana 32,33), "Eng qiyin savollar" (mavzu nomi va "0 % topdi"), "Viloyatlar bellashuvi" (30+ qatnashchi sharti) va "Reyting va statistika e'londa muzlatilgan" eslatmasi.
- **Mock reytingi (/mock/10/reyting).** "Test" va "O'sish" tablari, Respublika yoki viloyat filtri, podium, har qatorda ball va baho (B, C+ yoki "yo'q"). Teng ball — teng o'rin.
- **Natija va prognoz.** /natija hozircha bo'sh holatda: "Hali natija yo'q" va ikki tugma (Mock imtihon, Diagnostika). Prognoz reytingi /reyting/prognoz sahifasida.

API: `/me/mocks?subject=tarix`, `/library/mock-days`, `/library/mock/{sana}/live`, `/library/mock/{n}`, `/library/mock/{n}/rating?tab=test&scope=all`, `/library/mock/{sana}/stats`, `/me/prognoz`, `/attempts?mode=mock` va `mode=diagnostic`.

## Reyting, liga va nishonlar (/reyting)

Reyting ekrani to'rt tabdan iborat: Liga, Reyting (prognoz bo'yicha), Bellashuv va Nishonlar. Alohida /league sahifasi yo'q (404): liga /reyting'da, `/league` esa faqat API.

- **Liga.** Hero kartada aylanib suzuvchi 3D zumrad toshi, "Feruza ligasi: 21 ishtirokchi. Top 5 Zumrad ligasiga ko'tariladi. Bu hafta tushish yo'q", shanba 23:59 gacha taymer, o'rin (2-o'rin, 300 XP). Liga zinapoyasi: Feruza → Zumrad → Yoqut → Olmos.
- **Haftalik mukofotlar tangada.** 1-o'rin 300, 2-o'rin 200, 3-o'rin 100, top 5 ga ko'tarilish +100. "Hafta hozir yopilsa: 2-o'rin 200 + ko'tarilish 100 = +300" — foydalanuvchi aynan nima olishini ko'radi.
- **Jonli jadval.** XP bo'yicha, ko'tarilish chizig'i bilan, oxirida "yana 11 ishtirokchi". Ostida raqib nudge'i: "Makhmudova sizni quvmoqda! Farq atigi 90 XP. Bellashuvda yutsangiz, yana +60 XP olasiz" va "Bellashuvga chaqirish" tugmasi (bosilmadi).
- **Hafta yakuni (oldindan ko'rish sheet'i).** Katta tosh nurlar ichida, eski tosh chapga uchib kichrayadi, yangisi pastdan ko'tariladi, konfetti sochiladi. Mukofot summasi 0 dan sanaladi (count-up), balans "15 → 415". Pastda himoya: "Zumraddagi birinchi haftangizda tushmaysiz".
- **Reyting (prognoz).** Oxirgi reytingli mock prognozi bo'yicha 208 kishi. Filtrlar: Respublika, Viloyat, Tuman, Maktab, Guruh. Har qatorda ism, viloyat va tuman, prognoz ball, "yangi" belgisi va baho (A+, A, B+, B, C+). Mock topshirmaganlarga: "Reytingda o'rin olish uchun mock kerak".
- **Nishonlar va seriya.** Olov belgili seriya kartasi, haftalik 7 nuqta, "7 kunga 6 kun: +50 XP" va "1 qalqon" (seriya muzlatgichi). Besh haftalik seriya kalendari: faol kun, qalqon, o'tkazilgan kun. 15 nishon: Ilk mock, 7 va 30 kunlik seriya, Zumrad va Yoqut ligasi, Bellashuv g'olibi (5 g'alaba) va chempioni (20), Mukammal blok, A+ sari (70 ball), Saxiy qalb, Oy ustasi (20 kun), Kubok nishoni, hamda ona tili nishonlari (Esse yo'li, Esse ustasi, Punktuatsiya ustasi). Har nishonda progress: "1/7 kun", "0/5 g'alaba".

API: `/league`, `/rating?scope=all`, `/me/badges`.

## Profil va sozlamalar (/profil)

Profil — bir sahifali boshqaruv paneli: o'zlik, progress, iqtisod, tarif va sozlamalar bitta skrollda turadi. Hech bir sozlama o'zgartirilmadi.

- **Hero.** Osmon fonida bulutlar va uchayotgan qog'oz samolyot, markazda avatar, ism yonida qalam (tahrir). Ostida "11-sinf, Qashqadaryo, Mezon ID 201 948" va chiplar: liga va o'rin, seriya, tarif (Start).
- **Profilni bezash (/me/look).** Qora CTA "Profilni bezash, 2 ta buyum" → "Buyumlarim" bottom sheet. Yuqorida reyting qatoridagi ko'rinishingiz preview'i ("Reytingda, bellashuvda va ustoz ro'yxatida shunday ko'rinasiz"), so'ng Ism uslubi / Ramka / Muqova tablari, "Kiyilgan" belgisi, "Yana 13 ta do'konda" va "Saqlash".
- **Uchta statistika.** Prognoz ("Mockdan keyin", maqsad A+ 70), bu haftagi XP, tanga (bugun 15 / 200).
- **Vitrina va To'plamim.** Nishonlar 0/15; 29 buyumdan 2 tasi: ism uslublari 1/14, ramkalar 0/9, muqovalar 1/6.
- **Ustozim va guruhim.** Guruhga kod bilan qo'shilish va "Ustoz bo'lish: o'quvchilaringiz uchun guruh oching, ustoz paneli bepul" (/sinf/boshlash).
- **Fanlaringiz va tariflari.** Har fan o'z tarifida. Tarix bo'yicha bugungi limitlar progress-barlarda: beshta bo'lim (har biri 0/80), § savol-javob 5/100, test 0/8, o'yinlar va mashq cheksiz. "Sanalmaydi" ro'yxati: kunlik takrorlash, o'qish, xaritalar, portretlar. Fanlararo limit: AI ustoz 1/10, bellashuv 0/15. "Ertaga 00:00 da yangilanadi, 8 soat 26 daqiqadan keyin". Ostida Pro upsell (59 000 so'm) va davr kartasi (Start 39 000 so'm).
- **Boshqa bloklar.** Sovg'a banneri, "Sertifikatlarim" (mock natijalari BMBA sertifikati tartibida), tezkor havolalar (Qo'llanma, Tahlil, AI ustoz, Mocklarim, O'yinlar), Xabarlar (jamoa bilan aloqa), To'lovlar tarixi, Promokod, Do'stlarni taklif qilish ("Har do'st uchun 4 kun Pro").
- **Men haqimda va sozlamalar.** Hudud, maqsad va imtihon sanasi (onboarding orqali: daraja, sana, kuniga necha daqiqa), darslik tanlovi, ism, bildirishnomalar (mock arafasi, seriya, aksiyalar), o'qish qulayligi (yozuv o'lchami), til, "Bellashuv va do'stlar" kaliti, bellashuv chaqiruvlari (Hammadan / Do'stlardan / O'chiq), seriya eslatmalari, "To'lovni ota-onam qiladi" (yuborilgan havola va muddati), Chiqish, Oferta, Maxfiylik.
- **Kvestlar.** Profilda alohida kvest bo'limi yo'q: kunlik vazifalar va sandiq bosh sahifada (`/me/quests`), uzoq muddatli maqsadlar nishonlar ko'rinishida.

API: `/me/about`, `/me/notifications`, `/me/region`, `/me/shop`, `/billing/value`, `/tarix/limits`, `/tarix/limits/plans`, `/qollanma`.

## Hamyon va do'kon (/hamyon, /dokon)

Tanga faqat o'qish bilan topiladi: pulga sotilmaydi, boshqaga o'tkazilmaydi va kuniga 200 tanga bilan cheklangan. Bu inflyatsiyani to'xtatadi va do'kondagi buyumni bir necha kunlik maqsadga aylantiradi. Hech narsa sotib olinmadi.

| Manba | Tanga |
| --- | --- |
| Kunlik vazifa (3 ta) | har biri 15 |
| Kunlik sandiq (uchala vazifadan keyin) | 45 |
| Bellashuv | g'alaba 10, durang 5 (kuniga 50 gacha) |
| Mock yoki namunaviy test, birinchi urinish | 50 |
| Mockda shaxsiy rekord | 100 |
| Seriya marralari (kunlik chegaradan tashqari) | 7 kun 100, 14 kun 150, 30 kun 300, 50 kun 400, 100 kun 1 000, 365 kun 3 000 |
| Pro tarifi | barcha manbalar 1,2 barobar, kuniga 240 gacha |

- **Hamyon ekrani.** Shaftoli rangli hero'da katta balans va "Pro bilan 1,2 barobar tezroq" chipi. "Bugun topildi 15 / 200" progress-bar ("Chegaragacha yana 185 tanga, 00:00 da yangilanadi"), uchta kichik karta: bu hafta, jami topilgan, 7 kunlik marra (+100). Ikki tab: "Tarix" (kunlar bo'yicha tranzaksiyalar, masalan "Kunlik vazifa: 1 bellashuv yoki o'yin, 13:29, +15") va "Qanday topiladi". Pastda: "Xaridni 24 soat ichida bekor qilish mumkin, tanga to'liq qaytadi".
- **Do'kon.** Tepada "Haftalik vitrina" (22–28-noyabr, yakshanba yangilanadi, buyumlar keyin yana qaytadi): katta preview va "Kiyib ko'rish" tugmasi, ostida 4 ta vitrina buyumi. Toifalar: Ramka (avatar atrofida), Ism uslubi (reyting, bellashuv, profilda), Muqova (profil tepasida), Foydali.
- **Noyoblik va narxlar.** Oddiy 300–500, Noyob 600–1 000, Ajoyib 1 200–2 000, Afsonaviy 2 500–4 000 tanga. Vaqtincha sotilmayotganlari "Yana qaytadi" belgisi bilan ko'rsatiladi (FOMO).
- **Foydali buyumlar.** +3 bellashuv (limitdan keyin, kuniga 1 marta) — 200; Seriya qalqoni — 200; Seriya garovi: 100 qo'yasiz, 7 kun uzilmasangiz 200 qaytadi.
- **Faxriy buyumlar (sotilmaydi, erishiladi).** Liga ramkasi (Olmos ligasida 1-o'rin), Olov ism uslubi (100 kunlik seriya), Elchi ramkasi (10 ta faol do'st), Kubok ramkasi (Mezon Kubogida top 10).

API: `/me/wallet`, `/me/shop`, `/me/name`.

## Tariflar, sovg'a va taklif (/tariflar, /sovga, /taklif)

Monetizatsiya uch pog'onali: Bepul, Start (39 000 so'm / 30 kun) va Pro (59 000 so'm / 30 kun, 3 oy 139 000 so'm). Tarif har fanga alohida olinadi, yangi foydalanuvchi 2 kunlik Start sinovini oladi. To'lov, promo-kod va sovg'a yuborish bosqichlariga o'tilmadi.

| Imkoniyat | Bepul | Start | Pro |
| --- | --- | --- | --- |
| Izoh va mock tahlili | yo'q | bor | bor |
| Mashq | 10 / kun | cheksiz | cheksiz |
| AI ustoz | 3 / kun | 10 / kun | 25 / kun |
| Bellashuv | 3 / kun | 15 / kun | cheksiz |
| Tarix: qo'llanma bo'limlari | 10 savol / kun | 80 / kun | cheksiz |
| Tarix: § savol-javob | 15 / kun | 100 / kun | cheksiz |
| Tarix: testlar | 1 / kun (10 savol) | 8 / kun | cheksiz |
| Tarix: o'yinlar | har o'yindan 2 raund | cheksiz | cheksiz |
| Mock | umrida 1 ta | davrda 7 ta | barcha haftalik |

- **Tariflar sahifasi.** "Nechta fan?" (1 / 2 / 3) va "1 oy / 3 oy (−21%)" almashtirgichlari. Start "Tavsiya" belgisi va "Nega xato qilganingizni tushuning" shiori bilan; narx yonida "kuniga 1 300 so'm". Imkoniyatlar Tushunish / O'rganish / Esse va yordam guruhlarida. Bepulda nima yo'qligi alohida ko'rsatiladi. Esse kreditlari: 1 ta 7 000, 5 ta 33 000, 10 ta 60 000 so'm. FAQ: fanni 7 kun ichida bir marta almashtirish, davr ichida fan qo'shishda proporsional to'lov formulasi, avtomatik yechib olinmaydi, tugashidan 3 kun oldin eslatma. To'lov Click va Payme orqali; "To'lovni ota-onangiz qilishi mumkin: havola yuboring".
- **Sovg'a (/sovga).** 3 qadamli usta: nima (Pro 1 yoki 3 oy, Start, esse kreditlari), qaysi fan, kimga (Do'stimga, Hamkasbimga, O'quvchimga, Ustozimga, Yaqin insonimga, Oilamga) va ism, so'ng tabriknoma. Oluvchi Mezonda bo'lmasa ham havoladan Telegram bilan bir bosishda kiradi; tarifi bo'lsa, kunlar qo'shiladi.
- **Taklif (/taklif).** Shaxsiy kod va qisqa havola (mezonapp.uz/t/KOD), "Nusxalash" va "Telegram'da ulashish". Do'st 1 kunlik Pro sinovini oladi; u birinchi to'lovni qilsa, sizga +4 kun Pro. Yiliga 12 mukofotgacha. "Qanday ishlaydi" 3 qadamda va taklif qilinganlar ro'yxati. Faqat yangi akkauntlar hisoblanadi.

API: `/billing/catalog`, `/billing/value`, `/billing/me`, `/tarix/limits/plans`, `/gifts/catalog`, `/referrals/me`.

## Bellashuv markazi (/bellashuv)

Hub ekrani ikki qadamli tanlov: avval bo'lim, keyin raqib turi. Jonli raqib qidiruvi boshlanmadi.

- **Bo'lim kartalari (2 ustunli to'r).** Aralash (9 212 fakt), Atamalar (2 556), Yillar (3 367), Shaxslar (1 888), Davlatlar va shaharlar (731), Shartnoma va urushlar (670). Har kartada bo'lim rangidagi ikonka, g'alabalar soni va radio-tanlov. Bitta bo'limga "Tavsiya" belgisi qo'yiladi va u oldindan tanlangan turadi.
- **Raqib turi.** "Tasodifiy raqib" / "Do'st bilan" segmenti. Ostida halollik va'dasi: "Hozir onlayn Tarix o'quvchisi. Faqat jonli raqib: bot ham, yozib olingan o'yin ham yo'q".
- **Qoidalar va limit.** "7 raund, har biri 10 soniya", "Bugun yana 15 ta bellashuv, Start: kuniga 15 ta", so'ng "Bellashuvni boshlash".
- Yuqori o'ng burchakda haftalik XP chipi, ya'ni bellashuv liga bilan bog'langani doim ko'rinib turadi.

API: `/duels/hub`, `/me/game/settings`, `/qollanma/bellashuv`.

## Desktop ko'rinishi va qo'shimcha ekranlar

1280 px kenglikda ilova chap sidebar va kontent tuzilishiga o'tadi, mobil pastki panel yo'qoladi. Kontent kartalari o'sha, faqat ikki ustunga taqsimlanadi.

- **Sidebar.** Guruhlar: O'RGANISH (Qo'llanma, Darsliklar, Mashq, AI ustoz), IMTIHON (Mock "Yakshanba" yorlig'i bilan, Natija va tahlil), O'YIN (Reyting, O'yinlar, Do'kon). Pastda tarif kartasi ("Start, Sinov, 2 kun qoldi", progress va "Start'ni saqlab qolish") va foydalanuvchi.
- **Yuqori panel.** Sahifa sarlavhasi va sana, "Mavzu yoki qism qidirish" qidiruvi, seriya, XP va tanga chiplari.
- **Bosh sahifa.** Noyabr Kubogi banneri ("Start va Pro o'quvchilari bellashadi, 23 sovrin", "Taxminan 40-o'rin, 50 ochko", "Qatnashish"). Kunlik vazifalar chapda ro'yxat, o'ngda katta qulflangan sandiq.
- **Xarita.** Desktop'da kengaytirilgan: davr tablari (Qadimgi davr, O'rta asrlar, XIX asr xonliklari), "Mil. avv. 3000-yil holati", "Darslik xaritalari" tugmasi, pastda Viktorina va Legenda panellari. Manba: Cliopatria (Seshat, CC BY 4.0) va Natural Earth.
- **AI ustoz (/ustoz).** "Qaysi mavzu qiziqtiradi?", davrlar bo'yicha tayyor savollar, "Har javobda manba ko'rsatiladi", "Metodistlar bazasi" belgisi, "Bugun 9 ta savol qoldi". Savol berilmadi. API: `/tutor/threads`, `/tutor/quota`, `/tutor/suggestions`.
- **Mobil menyuda ko'rinmagan sahifalar:** /natija (Natija va tahlil), /dokon, /seriya, /sertifikatlar, /mocklarim, /xabarlar, /promokod.

## Gamifikatsiya va o'rganish metodikasi

Mezonning asosiy siri — bir-biriga ulangan to'rt xil vaqt halqasi. Har kuni vazifalar va takrorlash, har hafta liga, har oy kubok, oxirida esa mock va imtihon. Har bir halqa o'quvchini keyingi kunga qaytaradi.

| Halqa | Mexanika | Mukofot |
| --- | --- | --- |
| Kunlik | 3 ta vazifa (5 savol, 8 ta to'g'ri, 1 o'yin yoki duel); bugungi o'yin yo'li; kunlik takrorlash; "Bugun tarixda" savoli | Har vazifa +15 tanga; sandiq (45 tanga); yo'l uchun +30 XP; olov streak |
| Haftalik | Ligalar (birinchisi "Feruza ligasi"), XP bo'yicha reyting; haftalik o'yin kalendari | Ligada ko'tarilish; o'yinlar xilma-xilligi statistikasi |
| Oylik | "Noyabr Kubogi" (ochko faqat o'zingizga ko'rinadi); "Noyabr ustasi" — 20 kun faol bo'lish | Nishon (badge) |
| Imtihon | Haftalik Mock (yakshanba 20:00, sanoq taymeri, ishtirokchilar soni va hududi); ball prognozi; A+ maqsad | Prognoz (masalan, 57,9 · B, "A+ gacha 12,1 ball") |

**Valyutalar.** XP (o'yin va mashqlardan, liga uchun) va tangalar (vazifalar va sandiqdan). API'da `/me/wallet`, `/me/shop`, `/me/look` endpointlari bor: tangalarga avatar va ko'rinish narsalari sotib olinadi.

**Interval bilan takrorlash (SRS).** Har bir fakt to'rt holatdan birida bo'ladi: Yangi, O'rganilmoqda, Takrorlash kerak, O'zlashtirildi. Javobdan keyin foydalanuvchi o'zi baho beradi ("Bildim" yoki "Bilmadim"). Keyingi ko'rsatish vaqti shu bahoga qarab belgilanadi (10 daqiqa yoki 4 kun). Kunlik takrorlash navbati bosh sahifaga va qo'llanmaga chiqariladi.

**Faol eslash.** Savol-javob rejimida javob darhol ko'rsatilmaydi: "Avval o'zingiz eslang". Bu tamoyil kartochkalar, test va o'yinlarning hammasida takrorlanadi.

**Har bir javob darslikka bog'langan.** Har bir fakt, xato yoki natija ostida "8-sinf Jahon tarixi (2024), 10-mavzu, 63-bet" kabi havola bor. Yangi va eski darslik (2017–2019) o'rtasida almashtirish mumkin. Bu ishonch uyg'otadi va o'quvchini kitobga qaytaradi.

**Moslashuvchan qiyinlik.** Vaqt chizig'ida "Keyingi raundda sanalar bir-biriga yaqinroq bo'ladi". Bugungi o'yin yo'li esa oxirgi 7 kunda zaif bo'lgan ko'nikmalardan tuziladi.

**Freemium modeli.** Uch tarif bor: Bepul, Start va Pro (batafsil — "Tariflar, sovg'a va taklif" bo'limida). Sinov davrida Start limitlari amal qiladi: bo'lim faktlari 80/kun, savol-javob 100/kun, test 8/kun, bellashuv 15/kun. Pro tarif 59 000 so'm va limitlarni olib tashlaydi. O'qish, darslik beti, kunlik takrorlash va xaritalar limitga kirmaydi. Limitlar Toshkent vaqti bilan 00:00 da yangilanadi. Bundan tashqari: ota-ona to'lashi uchun havola (7 kun amal qiladi), sovg'a qilish (60 kun ichida olinadi), promo-kod va referal (`/taklif`).

**Ijtimoiy isbot.** Mock kartasida 47 ta qatnashchi va "Qashqadaryodan 4 kishi" yozuvi chiqadi. Reyting, duellar va do'stni chaqirish ham shu maqsadga xizmat qiladi.

## Animatsiyalar

Ilovada 1 210 ta CSS `@keyframes` bor va ularning birortasi ham kutubxonaga tayanmaydi. Animatsiyalar uch qatlamga bo'linadi: fondagi doimiy "hayot", kirish va paydo bo'lish harakatlari hamda javobga beriladigan feedback. `prefers-reduced-motion` uchun 80 ta qoida yozilgan.

**Fondagi doimiy harakat (cheksiz, sekin)**

| Nomi | Kodi | Vaqti |
| --- | --- | --- |
| osmon-float | `translate: 0 -8px` va qaytish | 3.3–3.4s |
| osmon-drift (bulutlar) | `translate: 14px` va qaytish | 10s |
| osmon-twinkle (yulduzlar) | `scale(.5)→scale(1) rotate(45deg)`, opacity .45→1 | 2.6s |
| osmon-dash (yo'l chizig'i) | `stroke-dashoffset: -22px` | 1s |
| osmon-fly (qog'oz samolyot) | `offset-path` egri chizig'i bo'ylab `offset-distance` 0→100% | 9s |
| clay-lift (personaj) | `translateY(-5px) rotate(-4deg)` | 3.3s |
| osmon-blink (ko'z qisish) | 92–100% oralig'ida `scaleY(1→.1→1)` | 4.2s |
| osmon-hatch (progress shtrixi) | `background-position` siljishi | 1.5s |

**Kirish va paydo bo'lish (bir martalik)**

- `osmon-rise`: pastdan 16px ko'tarilib paydo bo'lish (0.8s). Sahifa bloklari skroll paytida birma-bir shunday chiqadi.
- `osmon-pop`: `scale(.4)→1` (chip va belgilar uchun).
- `stol-sheet-up`: bottom sheet `translateY(100%)→none`.
- Logotipdagi tarozi (`BrandMark rock / settle`): splash ekranda tarozi pallalari tebranib, so'ng muvozanatga keladi.

**Feedback (javobga)**

- To'g'ri javob: `ok-ring` halqasi, variant yashil rangga kiradi, ✓ chiqadi.
- O'yinlar (`tarix-oyin` moduli): `pop`, `rise`, `fade`; asrlar o'yinida `asr fill` va `rom` (rim raqami).
- "Kim men?" portreti: `portret spin` va `bob`, karta ochilishi.
- Duel: `tug` (arqon), `screenShake`, `vsText`, `confetti`, `trophy`, `crown`.
- Sovg'a va to'lov: `gift-lid`, `gift-flap`, `billing glint`, `badgePop`.
- Sertifikat: `unfold`, `stamp` (muhr), `qrin`, `shine`.

### O'yin va liga animatsiyalari (ikkinchi sessiya)

Har o'yinning o'z CSS moduli bor, umumiy harakatlar esa `tarix-oyin` modulida (rise, pop, shake, okring, sheet, draw, burst, pulse, grow). Ko'p keyframe ikki nusxada yozilgan (pop / pop2, shake / shake2): holat o'zgarganda nom almashtiriladi va animatsiya qaytadan boshlanadi.

| Nomi | Kodi | Qayerda |
| --- | --- | --- |
| oldin: count | scale(1.8) → 1, opacity 0 → 1 | 3-2-1 sanoq |
| oldin: float | translateY(6px) scale(.8) → scale(1.08) → yuqoriga so'nish | "+10" ochko uchib chiqadi |
| oldin: burst, okring | scale .8 → 1.9 va .9 → 1.35, opacity → 0 | to'g'ri javob halqasi |
| shake (barcha o'yinlar) | translateX −7, 6, −4 … px | xato javob |
| juftlik: draw, glow | stroke-dashoffset → 0; stroke-width 3 ↔ 6px | juftlarni ulovchi chiziq chiziladi va porlaydi |
| bingo: line, big, miss | stroke-dashoffset → 0; scale(1.8) rotate(−8deg) → rotate(−3deg); box-shadow 2 ↔ 5px | bingo chizig'i, "BINGO" yozuvi, o'tkazib yuborilgan katak |
| kqq: stamp, rost: stamp | scale(1.7) rotate(−18deg) → scale(1) rotate(−6deg) | "Muhr bosildi", rost/yolg'on muhri |
| kqq: sword | rotate(−14deg) scale(.8) → none | qilich belgisi |
| xarita: wave, glow, dash | scale .2 → 3.4 to'lqin; stroke 3.5 ↔ 6px; dashoffset −26px | bosilgan nuqtadan to'lqin, to'g'ri hudud porlashi, yurish yo'li harakati |
| atama: wave, in | translateY(−10px) scale(1.12); translateY(16px) scale(.7) → none | to'g'ri so'z harflari to'lqini; plitka qaytishi |
| Xotira kartasi | transition transform .5s cubic-bezier(.2,.8,.2,1), perspective 700px, rotateY(180deg), backface-visibility: hidden | karta ochilishi |
| ortiqcha: band | scale(1.4) rotate(−4deg) → rotate(−2deg) | "Uchalasi: …" lentasi |
| rost: read | scaleX 1 → 0 | izohni o'qish vaqti chizig'i |
| l2: l2Old, l2Rise, l2Conf, kRays, kBump | translate(−112px) scale(.55); translateY(60px) → 0; konfetti; 360° nurlar; scale 1.22 | liga ko'tarilishi oynasi, mukofot summasining count-up'i |
| l1: p7Gem, p7Crown, p7Ping | translateY(−7px) rotate(±3deg); rotate(±6deg); scale .5 → 1.5 | liga kartasidagi suzuvchi tosh, toj, "jonli" nuqta |

**Qo'llangan texnikalar (o'zingizda takrorlash uchun)**

1. **Salbiy `animation-delay`** (−1s, −2s, −5s). Bir xil animatsiyali elementlar turli fazada boshlanadi va sinxron "marsh" qilmaydi.
2. **Alohida `translate` xususiyati.** U `transform` bilan to'qnashmaydi, shuning uchun bitta element bir vaqtning o'zida suzishi va aylanishi mumkin.
3. **CSS `offset-path`.** Yo'l bo'ylab uchish JavaScript'siz amalga oshiriladi.
4. **SVG ichidagi `<g>` guruhlarini alohida animatsiya qilish.** Personajning tanasi ko'tariladi, ko'zlari esa alohida ochilib-yumiladi.
5. **Har bir ekran uchun alohida CSS Module.** Nomlar to'qnashmaydi, keraksiz CSS ham yuklanmaydi.
6. **Reduced motion.** Har bir doimiy animatsiya uchun o'chirish qoidasi yozilgan.

## Ma'lumot modeli va API

Ilovaning markazida bitta jadval turadi: **fakt**. Qolgan hamma narsa (o'yin, test, qo'llanma, takrorlash) shu faktlarga bog'lanadi. Quyidagi model ekranlarda ko'ringan maydonlardan tiklangan.

| Obyekt | Asosiy maydonlar (ekranlardan tiklangan) |
| --- | --- |
| Darslik (book) | id, sinf (5–11), fan (O'zbekiston tarixi, Jahon tarixi, Qadimgi dunyo, Hikoyalar), nashr yili, yangi yoki eski nashr, boblar → § (raqami, nomi) |
| Fakt (fact) | id, turi (sana, shaxs, atama, joy, urush yoki shartnoma, asar, voqea), sana matni ("XIV asr boshlari", "mil. avv. 539"), tartiblash uchun yil soni, davr (Qadimgi, O'rta asrlar, Yangi, Eng yangi), matn, manba (darslik id, § yoki mavzu, bet), qo'shimcha manba (eski darslik) |
| Shaxs | fakt + kategoriya (hukmdor, olim, shoir, sarkarda, sayyoh, davlat arbobi), portret URL yoki bo'sh, qisqa tavsif, ishoralar ("Kim men?" uchun 3 ta) |
| Urush yoki shartnoma | fakt + kichik tur (jang, urush, shartnoma, qo'zg'olon), tomonlar (A, B), g'olib, natija |
| Joy | fakt + tur (shahar yoki hudud), xaritadagi koordinata (sxematik x, y), xarita qatlami (XVI asr, XVIII–XIX asr) |
| Savol (question) | § id, turi (yillar, shaxslar, atamalar, joylar, voqealar, asarlar), savol, javob, 3 ta noto'g'ri variant, "ustoz tanlovi" belgisi |
| Foydalanuvchi faktining holati | user, fact, holat (yangi, o'rganilmoqda, takrorlash kerak, o'zlashtirildi), keyingi ko'rsatish vaqti, oraliq, xatolar soni |
| Kunlik hisob | user, sana, bo'lim, ishlatilgan limit, XP, o'yinlar |
| Mock | sana, vaqt, fan, ro'yxatdan o'tganlar, natija, prognoz |

**Kuzatilgan API endpointlar** (bazaviy manzil `https://api.mezonapp.uz/api/v1`):

| Guruh | Endpointlar |
| --- | --- |
| Auth | `/auth/telegram/miniapp`, `/auth/telegram/widget`, `/auth/otp/request`, `/auth/otp/verify`, `/auth/refresh`, `/auth/logout` |
| Profil | `/me`, `/me/summary`, `/me/subjects`, `/me/plan`, `/me/path`, `/me/prognoz`, `/me/pulse`, `/me/xp?days=7`, `/me/notifications`, `/me/name`, `/me/region` |
| Gamifikatsiya | `/me/quests`, `/me/quests/chest`, `/me/game`, `/me/kubok`, `/me/kubok/card`, `/me/badges`, `/me/wallet`, `/me/shop`, `/me/look`, `/league`, `/rating` |
| Tarix kontenti | `/qollanma`, `/qollanma/bugun`, `/qollanma/shelf`, `/qollanma/sessions`, `/tarix/albom?limit=12&due_first=true`, `/tarix/oyin`, `/tarix/limits`, `/tarix/limits/plans`, `/library?format=tarix_milliy` |
| O'yin va duel | `/games/catalog`, `/games/today`, `/qollanma/bellashuv`, `/duels/hub`, `/duels/queue`, `/duels/random`, `/duels/invites` |
| Mock | `/library/mock-days?subject=tarix`, `/library/mock/{sana}/live?subject=tarix` |
| To'lov | `/billing/catalog`, `/billing/me`, `/billing/quote`, `/billing/checkout`, `/billing/promo/redeem`, `/billing/parent-links`, `/billing/gift-days/activate` |
| Boshqa | `/referrals/me`, `/me/channel-invite`, `/content-reports` (foydalanuvchi xato haqida xabar beradi) |

Ikkinchi sessiyada qo'shimcha kuzatilgan endpointlar: o'yin sessiyalari `/tarix/oyin/{tur}/start`, `/tarix/oyin/sessions/{id}/act/{harakat}`, `/tarix/oyin/sessions/{id}/answer`, `/tarix/oyin/sessions/{id}/finish`; mock `/me/mocks`, `/library/mock/{n}`, `/library/mock/{n}/rating`, `/library/mock/{sana}/stats`, `/attempts?mode=mock|diagnostic`; boshqalar `/me/about`, `/me/game/settings`, `/billing/value`, `/gifts/catalog`, `/tutor/threads`, `/tutor/quota`, `/tutor/suggestions`, `/writing/quota`. Xato javobi namunasi: `/me/plan` → `{detail: {code: "plan_unavailable", message: "Bu fan uchun kunlik reja keyingi bosqichda qo'shiladi"}}`.

Muhim qaror: kunlik limitlar va SRS jadvali server tomonda hisoblanadi (`/tarix/limits`, `due_first=true`). Klient faqat ko'rsatadi, shuning uchun limitni aldab o'tib bo'lmaydi.

## Kamchiliklar va sizning imkoniyatlaringiz

Mezon kuchli, lekin uning tarix moduli hali beta bosqichida va kontent sifatida aniq xatolar bor. Bu sizga raqobatda ustunlik olish uchun eng qulay joy.

**Tahlil vaqtida ko'rilgan xatolar**

| Joy | Muammo |
| --- | --- |
| Yillar → Vaqt o'qi | Birinchi asr "mil. avv. CCCCCCCCCC asr" bo'lib chiqqan; bosilganda "Qo'llanma ochilmadi. Ma'lumot noto'g'ri to'ldirilgan" xatosi chiqadi. Asrlar soni ham bir yuklanishdan boshqasiga o'zgargan (3 367 va 3 766) |
| Savol-javob, §1, 3-savol | "Bu qaysi atama?" savoli ta'rifni beradi, "javob" sifatida esa o'sha ta'rif qayta ko'rsatiladi. Atamaning o'zi ("manbashunos") faqat test rejimida chiqadi |
| Shaxslar | Abdulla Oripov "Qadimgi dunyo" davriga belgilangan |
| Shaxs kartasi → Zamondoshlari | Zamondoshlar faqat bir xil davr teglari bo'yicha tanlanadi: 1717-yildagi Bekovich-Cherkasskiyga 1860–1880-yillardagi Kaufman va Skobelev "zamondosh" qilib ko'rsatilgan |
| "Kim men?" ishoralari | Bahodir Jalolov uchun 2-ishora "Rassom yoki haykaltarosh (12-§ dagi bokschi bilan bir xil ism)" — adashtirilgan adashlar |
| Faktlar matni | "Ulug'bek akademiyasi XIV asr (matnda shunday)" kabi tahrir izohlari foydalanuvchiga ko'rinib qolgan |
| Mashq markazi | "Tarix savollari qo'shilmoqda" — mavzu kodlari bo'yicha rasmiy test banki hali yo'q |
| Oferta | Xizmatlar faqat "Ona tili va adabiyot" deb yozilgan, ilova esa beshta fanni qamraydi |
| Ortiqchasini top | "Amir Temur (Sohibqiron)" Mehmed I va Usmon I bilan birga "Usmoniylar sulolasi hukmdorlari" deb guruhlangan. Bu o'yin ichidagi eng jiddiy fakt xatosi |
| O'yinlardagi darslik manbasi | Bitta element uchun o'yin ichidagi va natija oynasidagi bet har xil (A. Guterrish: 9-sinf Jahon tarixi, 25-mavzu va 5-sinf Tarixdan hikoyalar, §49). Ba'zi juftlarga boshqa faktning manbasi biriktirilgan: Mahmud Qoshg'ariyga Narshaxiy beti, Habibulloh Solihga Navro'z beti, Ishtvan Buyukka Temur mavzusi |
| Rost yoki yolg'on | "1521-yil 6-mart: Magellan Mariana va Filippin orollariga yetdi va jangda halok bo'ldi" — ikki voqea (6-mart va 27-aprel) bitta sanaga qo'shilgan. Magellan haqidagi fakt bir raundda ikki marta chiqdi |
| Qaysi biri oldin?, Tarix bingo | Voqea o'rniga davlat nomi beriladi ("Fransiya" → 843, "Tohiriylar davlati") yoki kontekstsiz gap ("Ikki hukmdor o'rtasida uch marta jang bo'lgan", "Bu hududlarga mo'g'ul bosqinlari boshlandi") |
| Kim? Qachon? Qayerda? | Bema'ni chalg'ituvchilar javobni topishni osonlashtiradi ("Toshkent shahar boshlig'i S. Putinsev Litvani", "Shvetsiya Maderoni"). Rus-Litva urushi (1514) uchun "Kim kimni yengdi?" ikki ma'noli. Sahifa 10 soniyadan ko'proq skelet holatida turdi |
| Xotira | Yopiq kartalar matni DOM'da bor: inspektor yoki ekran o'quvchi bilan javoblar ko'rinadi. Taymer sessiya yaratilgan paytdan sanaydi (174:22) |
| Xotira, Juftlik | Qo'sh qo'shtirnoq: "««Uloqda»»", "««Temur» operasi»" |
| Natija oynasi | Kunlik 300 XP chegarasi to'lganda ham "har biri 3 XP: +1 XP" va "2-raund ham XP to'liq" degan qarama-qarshi matn chiqadi |
| Xarita, Yurish yo'li | Boshlang'ich ko'rinishda 4 marshrutdan 1–2 tasi ko'rinadi, qolganlari ekran chetida; xarita bir necha soniya bo'sh turadi |
| Mock ro'yxati | "Quadro" va "Qadro" jamoasi; "№4 Mock №9 testi", "№5 Mock №10 testi" raqamlari mos emas. Mock №10 uchun turli sahifalarda 26 va 68 qatnashchi (o'rtacha 30,70 va 29,5) |
| Hamyon | "3 ta vazifa, har biri 15 tanga" yonida "+3" belgisi |
| Liga | Ko'tarilish zonasi "Chiqish zonasidasiz" deb yozilgan; /league manzili 404 |
| Nishonlar va seriya | Tarix fanida ona tili nishonlari (Esse yo'li, Punktuatsiya ustasi) chiqadi; haftalik seriya qatorida o'tgan kunlar "Hali boshlanmagan" |
| Sovg'a | Tarix tanlanganda ham esse kreditlari taklif qilinadi, holbuki esse faqat ona tilida |
| AI ustoz | Tarix sahifasi /practice/catalog?format=ona\_tili\_milliy so'rovini yuboradi |
| Profil | Prognoz kartasida "Maqsad A+ (70)", sozlamalarda "Maqsad: B" |
| Sessiya | Sahifa qayta yuklanganda sessiya tugab, Telegram orqali qayta kirish so'raldi |

**Siz qanday ustunlik olishingiz mumkin**

1. **Kontent sifati.** Har bir faktni metodist tekshiradi va "tekshirilgan" belgisi qo'yiladi. Avtomatik tuzilgan savollar uchun validatsiya qilinadi: javob savol matnini takrorlamasligi, asr va davr yil bilan mos kelishi, zamondoshlar yillar kesishuvi bo'yicha tanlanishi kerak.
2. **Rasmiy imtihon formati.** Milliy sertifikat (BMBA) spetsifikatsiyasi bo'yicha mavzu kodlari, topshiriq turlari va ball tizimi bilan to'liq test bankini birinchi kundan bering. Bu Mezonda hali yo'q.
3. **Bitta aniq xarita qatlami.** Mezon Xarita mashqida haqiqiy chegaralarni (Cliopatria/Seshat, Natural Earth) ishlatadi, qo'llanmadagi xarita esa sxematik. Siz bitta aniq, davr kesimli xaritani qo'llanma, o'yin va testda bir xil ishlating, yurish yo'llarini esa avtomatik zoom bilan to'liq ko'rsating (masalan, Amir Temur yurishlari).
4. **Izohli xato tahlili.** Har bir xato uchun "nega bu javob noto'g'ri" degan qisqa sabab bering, faqat darslik beti bilan cheklanmang.
5. **Faqat tarixga ixtisoslashish.** Mezon beshta fanni qamraydi; siz tarix bo'yicha chuqurroq bo'lishingiz mumkin: xronologik xaritalar, sulolalar shajarasi, manbalar bilan ishlash topshiriqlari.
6. **Ustoz va sinf rejimi.** Mezonda bu kodda bor, lekin ochiq emas. Maktab ustozlari uchun guruh, topshiriq va hisobot vositalarini erta bering.

## Yo'l xaritasi

Mezon tajribasi shuni ko'rsatadi: ilovaning qiymati kontent bazasi va takrorlash tizimidan keladi, o'yinlar va raqobat esa shu poydevor ustiga quriladi. Shuning uchun MVP'ni fakt bazasi va SRS'dan boshlang. Muddatlar taxminiy va kichik jamoa uchun hisoblangan.

&#91;embedded content: yo'l xaritasi · 3 bosqich\]

Birinchi bosqichda Mezondagi xatolarni takrorlamaslik uchun kontent validatsiyasini ham shu yerga qo'shing (oldingi bo'limga qarang).

**Hali o'rganilmagan bo'limlar.** Ikkinchi sessiyadan keyin faqat taqiqlangan yoki resurs sarflaydigan harakatlar ortidagi ekranlar qoldi:

- Mock jarayoni: ro'yxatdan o'tish, imtihon interfeysi, natija, prognoz va sertifikat ekranlari (/natija hozircha bo'sh)
- Bellashuv jarayoni: raqib qidirish, raundlar va natija (jonli raqib talab qilinadi)
- To'lov oynasi va checkout, promo-kod, sovg'aning 2–3-qadamlari (tabriknoma, havola)
- Ustoz paneli (/sinf, guruhlar, topshiriqlar)
- AI ustoz javoblari sifati (savol limiti sarflanadi)
- Kim men? va Asrlarga ajratning 2-raundi, Onboarding, /seriya, /sertifikatlar, /xabarlar sahifalari

Ularni alohida, ruxsat berilgan sessiyada ko'rib chiqish mumkin.
