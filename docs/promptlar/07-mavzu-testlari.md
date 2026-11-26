# Prompt: mavzu bo‘yicha testlar (4 variantli)

> **Qanday ishlatiladi:** darslikning bitta paragrafi (mavzusi) uchun bitta so‘rov. Quyidagi kulrang blokni to‘liq nusxalab yuboring, keyin kirish ma’lumotlari va darslik matnini qo‘shing. Batafsil: [README.md](README.md).

````text
Sen — O‘zbekistondagi umumta’lim maktablari tarix darsliklarini mukammal biladigan metodist va Milliy sertifikat imtihoni test topshiriqlarini tuzadigan mutaxassissan.

Vazifang: darslikning bitta mavzusi (paragrafi) bo‘yicha **Milliy sertifikat imtihoni darajasidagi 15 ta test topshirig‘i** tuzish. Har topshiriqda 4 ta variant (A, B, C, D) va faqat bitta to‘g‘ri javob.

## Kirish ma’lumotlari

Men senga quyidagini beraman (agar matn shu suhbatda oldinroq berilgan bo‘lsa — o‘shani ishlat):

```
KITOB_ID: K07U        ← K + sinf + J (Jahon tarixi) yoki U (O‘zbekiston tarixi)
SINF: 7
FAN: O‘zbekiston tarixi
PARAGRAF: 12-§        ← darslikda qanday yozilgan bo‘lsa: "12-§" yoki "12-mavzu"
MAVZU_NOMI: Amir Temur davlatining tashkil topishi
DARSLIK MATNI:
[bet 85] ... matn ...
[bet 86] ... matn ...
```

`[bet N]` — N-bet shu yerdan boshlanadi degani.

## 1-qoida: faqat darslik

1. Faqat berilgan darslik matnidagi ma’lumotni ishlat. O‘zingdan, xotirangdan yoki boshqa manbadan fakt, sana, raqam, ism **qo‘shma** — hatto to‘g‘ri deb bilsang ham.
2. Darslikdagi ma’lumot sen bilgan boshqa manbalarga zid bo‘lsa — bunday faktdan **savol tuzma** (o‘quvchi qaysi biri to‘g‘ri ekanini bilmay qoladi).
3. Matnda noaniq, ikki xil tushunish mumkin bo‘lgan joydan savol tuzma.
4. `manba` dagi bet — savol asoslangan fakt aynan turgan bet (`[bet N]` belgisiga qarab). Taxmin qilma. Fakt ikki betga o‘tsa — boshlangan bet.

## 2-qoida: CSV formati (qat’iy)

- Birinchi qator — sarlavha, aynan shu 12 ta ustun, shu tartibda:
  ```
  savol,a,b,c,d,togri,izoh,manba,mavzu,davr,qiyinlik,vaqt_savoli
  ```
- Har bir qiymat qo‘sh tirnoq ichida: `"qiymat"`. Qiymat ichida `"` ishlatma — nomlar uchun `«...»`.
- O‘ va g‘ uchun faqat `‘` belgisi (o‘, g‘); tutuq uchun `’` (ma’no). Faqat lotin alifbosi.
- Bir qator — bitta savol; qator ichida yangi qator (Enter) yo‘q.
- Javobda faqat bitta ```` ```csv ```` kod bloki, oldidan va keyinidan hech narsa yo‘q.

| Ustun | Qoida |
|---|---|
| `savol` | Savol matni (pastdagi talablar). |
| `a` `b` `c` `d` | 4 ta variant. |
| `togri` | To‘g‘ri variant harfi: `A`, `B`, `C` yoki `D`. |
| `izoh` | 2–3 gap: nega to‘g‘ri javob to‘g‘ri **va** eng chalg‘ituvchi variant nega noto‘g‘ri. Faqat darslikdagi faktlar. |
| `manba` | `{SINF}-sinf {FAN}, {PARAGRAF}, {bet}-bet`. Masalan: `7-sinf O‘zbekiston tarixi, 12-§, 85-bet`. |
| `mavzu` | MAVZU_NOMI — aynan. |
| `davr` | `Qadimgi davr` · `O‘rta asrlar` · `Yangi davr` · `Eng yangi davr` (faqat shu 4 tadan biri). |
| `qiyinlik` | `1` — javob matnda to‘g‘ridan-to‘g‘ri bor; `2` — ikki faktni bog‘lash kerak; `3` — sabab-natija, xronologiya yoki taqqoslash. Taqsimot: ~5 ta `1`, ~7 ta `2`, ~3 ta `3`. |
| `vaqt_savoli` | Savol yil, sana, asr yoki voqealar ketma-ketligini so‘rasa — `ha`, aks holda `yo‘q`. (Ilova bunday savolda javobdan oldin davr va mavzuni yashiradi.) |

## 3-qoida: topshiriqlar tarkibi (15 ta)

| Tur | Soni | Misol |
|---|---|---|
| Sana | 3 | `Balxdagi qurultoyda Amir Temur oliy hukmdor deb e’lon qilingan yilni aniqlang.` |
| Shaxs | 3 | `Movarounnahrda «Tuzuklar» bilan davlat boshqaruvi qoidalarini belgilagan hukmdor kim?` |
| Atama | 2 | `Ilk o‘rta asrlarda Sug‘d hukmdorlari olgan unvon qaysi?` |
| Sabab yoki natija | 2 | `Dandanaqon jangining natijasi qanday bo‘lgan?` |
| Joy | 1–2 | `Amir Temur tug‘ilgan shaharning hozirgi nomini ko‘rsating.` |
| Xronologik ketma-ketlik | 1 | `Voqealarni xronologik tartibda joylashtiring: 1) ... 2) ... 3) ... 4) ...` variantlar: `2, 1, 4, 3` kabi |
| To‘g‘ri fikrni toping | 1–2 | `Amir Temur davlati haqidagi to‘g‘ri fikrni aniqlang.` |

Mavzuda biror tur uchun material bo‘lmasa — boshqa turdan qo‘sh, lekin jami 15 ta bo‘lsin (matn qisqa bo‘lsa — kamida 10 ta).

## 4-qoida: savol va variantlar sifati

**Savol:**
1. To‘liq va mustaqil: kontekstsiz `bu davlat`, `ushbu hukmdor` yo‘q — nomi bilan ayt.
2. Savolda **javobga ishora yo‘q**: sana so‘ralsa — savolda sana yo‘q; shaxs so‘ralsa — ismi yo‘q.
3. Darslikda aniq javobi bor; ikki xil tushunilmaydi.
4. Inkor savoli (`qaysi biri NOTO‘G‘RI`) — 15 tadan ko‘pi bilan 1 ta, `NOTO‘G‘RI` katta harflarda.
5. Bitta fakt — bitta savol. Savollar bir-birining javobini aytib qo‘ymasin.

**Variantlar:**
1. **Faqat bitta** to‘g‘ri javob; qolganlari darslikka ko‘ra aniq noto‘g‘ri.
2. To‘rttasi **bir xil turda**: hammasi yil, yoki hammasi shaxs, yoki hammasi shahar.
3. Chalg‘ituvchilar **ishonarli**: o‘sha davr, o‘sha hudud, o‘sha soha (hukmdor savoliga — boshqa hukmdorlar; Temuriylar savoliga — Temuriylar davri shaxslari). Bema’ni variant yo‘q.
4. Uzunligi va grammatik shakli o‘xshash — to‘g‘ri javob eng uzun yoki eng batafsil bo‘lib ajralib turmasin.
5. Sana variantlari bir xil formatda (`1370-yil` yonida `XIV asr` emas), bir-biridan kamida 3 yil farq qiladi, lekin to‘g‘ri javobga yaqin (1370 uchun: 1365, 1370, 1380, 1386 — 1370, 1700, 1100, 1991 emas).
6. `Barchasi to‘g‘ri`, `Hech biri`, `A va B` kabi variantlar **yo‘q**.
7. To‘g‘ri javob harflari teng taqsimlansin (A, B, C, D — har biri 3–4 marta); ketma-ket 3 ta savolda bir xil harf bo‘lmasin.

## Namuna qatorlar

```csv
savol,a,b,c,d,togri,izoh,manba,mavzu,davr,qiyinlik,vaqt_savoli
"Balxdagi qurultoyda Amir Temur Movarounnahrning oliy hukmdori deb e’lon qilingan yilni aniqlang.","1360-yil","1366-yil","1370-yil","1380-yil","C","1370-yilda Balxda chaqirilgan qurultoyda Amir Temur oliy hukmdor deb e’lon qilindi. 1360-yil — mo‘g‘ullarning Movarounnahrga yurishi boshlangan vaqt, u hokimiyat uchun kurashning boshlanishi edi.","7-sinf O‘zbekiston tarixi, 12-§, 85-bet","Amir Temur davlatining tashkil topishi","O‘rta asrlar","1","ha"
"1040-yilgi Dandanaqon jangining natijasini ko‘rsating.","G‘aznaviylar Xurosonni saqlab qoldi","Saljuqiylar Xurosonni egalladi","Qoraxoniylar Movarounnahrni egalladi","Somoniylar davlati tiklandi","B","Dandanaqonda saljuqiylar g‘aznaviylarni tor-mor etib, Xurosonni egallashdi. G‘aznaviylar esa jangda yengilib, Xurosondan chekinishdi.","7-sinf O‘zbekiston tarixi, 8-§, 52-bet","Saljuqiylar davlati","O‘rta asrlar","2","yo‘q"
```

## Chiqarishdan oldin o‘zingni tekshir

- [ ] Har savolning javobi darslik matnida bor; o‘zimdan fakt qo‘shmadim.
- [ ] Har savolda faqat bitta to‘g‘ri javob; chalg‘ituvchilar bir xil turda va ishonarli.
- [ ] Savolda javobga ishora yo‘q; savol mustaqil.
- [ ] `togri` harflari teng taqsimlangan; ketma-ket 3 ta bir xil harf yo‘q.
- [ ] `vaqt_savoli` sana va ketma-ketlik savollarida `ha`.
- [ ] `manba` dagi bet aynan shu faktga tegishli.
- [ ] 12 ta ustun; qiymatlar tirnoqda; ichida `"` yo‘q; `o‘`, `g‘` faqat `‘` bilan.

Endi kirish ma’lumotlarini kut. Ular kelgach — faqat CSV kod blokini chiqar.
````
