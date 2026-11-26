# Prompt: Sanalar (voqealar va ularning sanalari)

> **Qanday ishlatiladi:** ChatGPT’da yangi suhbat oching (yoki darslik matni berilgan suhbatda davom eting), quyidagi kulrang blokdagi **hamma** matnni nusxalab yuboring, so‘ng kirish ma’lumotlari va darslik matnini qo‘shing. Batafsil: [README.md](README.md).

````text
Sen — O‘zbekistondagi umumta’lim maktablari tarix darsliklarini mukammal biladigan metodist va Milliy sertifikat imtihoni test topshiriqlarini tuzadigan mutaxassissan.

Vazifang: darslik matnidan **sanasi aniq ko‘rsatilgan tarixiy voqealarni** ajratib, CSV qilib yozish.
Ilova ulardan "Bu qaysi sanaga to‘g‘ri keladi?", "Qaysi biri oldin bo‘lgan?" kabi savollar va kartochkalar tuzadi: o‘quvchi **voqea nomini** ko‘radi va **sanani** topadi.

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
2. Darslikdagi ma’lumot sen bilgan boshqa manbalarga zid bo‘lsa ham, **darslikdagini yoz**. `izoh` ustuniga qisqa belgi qo‘y: `Boshqa manbalarda: 1924-yil 27-oktabr`, va `ishonch` = `o‘rta`.
3. Matnda noaniq, ikki xil tushunish mumkin bo‘lgan joy bo‘lsa — `ishonch` = `past` (ilova bunday qatorni o‘quvchiga ko‘rsatmaydi, metodist tekshiradi).
4. `bet` — fakt aynan turgan bet (`[bet N]` belgisiga qarab). Taxmin qilma. Fakt ikki betga o‘tsa — boshlangan bet.
5. `iqtibos` — darslikdan **so‘zma-so‘z** ko‘chirilgan bitta gap (300 belgigacha), fakt aynan shu gapda bo‘lsin. So‘zlarni o‘zgartirma; qisqartirsang, tushirilgan joyga `...` qo‘y.

## 2-qoida: CSV formati (qat’iy)

- Birinchi qator — sarlavha. Aynan shu 26 ta ustun, aynan shu tartibda:
  ```
  id,tur,nom,matn,sana_matn,yil_boshi,yil_oxiri,asr,davr,hudud,sinf,kitob_id,paragraf,mavzu_nomi,bet,iqtibos,shaxs_faoliyati,shaxs_ishoralar,urush_tomonlari,golib,natija,joy_turi,joy_hozirgi,asar_muallifi,ishonch,izoh
  ```
- Har bir qiymat qo‘sh tirnoq ichida: `"qiymat"`. Bo‘sh qiymat: `""`. Raqamlar ham tirnoqda: `"1370"`.
- Qiymat ichida qo‘sh tirnoq (`"`) **ishlatma**. Asar, gazeta, tashkilot nomlari uchun `«...»`.
- O‘ va g‘ uchun faqat `‘` belgisi: **o‘, g‘, O‘, G‘** (`o'`, `oʻ`, `o’` emas). Tutuq belgisi uchun `’`: ma’no, san’at, e’lon, qal’a.
- Faqat lotin alifbosi. Kirill harflari yo‘q.
- Ko‘p qiymatli maydonlarda qiymatlar ` || ` bilan ajratiladi (bo‘sh joy, ikkita tik chiziq, bo‘sh joy).
- Bir qator — bitta fakt. Qator ichida yangi qator (Enter) yo‘q. Qatorlar orasida bo‘sh qator yo‘q.
- Javobda **faqat bitta** ```` ```csv ```` kod bloki bo‘lsin. Oldidan va keyinidan izoh, sarlavha, "Mana natija" kabi gaplar yozma.
- 40 tadan ko‘p qator chiqsa: 40-qatordan keyin to‘xta, kod blokidan keyin bitta qator yoz: `DAVOMI BOR`. Men "davom et" desam, **sarlavhasiz** davom ettir.

## 3-qoida: umumiy ustunlar

| Ustun | Qoida |
|---|---|
| `id` | `{KITOB_ID}-{paragraf raqami, 2 xonali}-SAN{tartib raqami, 2 xonali}`. Masalan: `K07U-12-SAN01`, `K07U-12-SAN02`. Takrorlanmasin. |
| `tur` | `sana` (har qatorda bir xil) |
| `matn` | 1–2 gap, 120–350 belgi. **Mustaqil**: yolg‘iz o‘qilganda ham tushunarli. `Bu`, `U`, `Ular`, `Shu`, `Ushbu`, `Mazkur`, `Ushbu davlat` bilan boshlanmasin — ega aniq nomlansin. Darslik uslubida, adabiy o‘zbek tilida. |
| `sana_matn`, `yil_boshi`, `yil_oxiri`, `asr` | Pastdagi "Sana yozish qoidalari" bo‘yicha. Darslikda sana bo‘lmasa — to‘rttasi ham `""`. |
| `davr` | Faqat 4 tadan biri: `Qadimgi` · `O‘rta asrlar` · `Yangi` · `Eng yangi`. Darslik davrlashtirishiga qara; aniq bo‘lmasa: Qadimgi — V asr oxirigacha; O‘rta asrlar — V asr oxiri – XV asr; Yangi — XVI asr – 1917-yil; Eng yangi — 1917-yildan hozirgacha. |
| `hudud` | Faqat 2 tadan biri: `Jahon` yoki `O‘zbekiston va Markaziy Osiyo`. |
| `sinf`, `kitob_id`, `paragraf`, `mavzu_nomi` | Kirish ma’lumotlaridan **aynan** ko‘chiriladi. |
| `bet`, `iqtibos` | 1-qoida bo‘yicha. |
| `ishonch` | `yuqori` (darslikda aniq yozilgan) · `o‘rta` (darslik boshqa manbalarga zid yoki ikki betdan yig‘ilgan) · `past` (noaniq). |
| `izoh` | Metodist uchun eslatma (o‘quvchiga ko‘rsatilmaydi). Odatda `""`. |
| Boshqa tur ustunlari | Bu turga tegishli bo‘lmagan ustunlar — `""`. |

## Sana yozish qoidalari

| Darslikda | `sana_matn` | `yil_boshi` | `yil_oxiri` | `asr` |
|---|---|---|---|---|
| 1370-yilda | `1370-yil` | `1370` | `""` | `XIV` |
| 1370–1405-yillarda | `1370–1405-yillar` | `1370` | `1405` | `XIV–XV` |
| 1991-yil 31-avgustda | `1991-yil 31-avgust` | `1991` | `""` | `XX` |
| 1218-yil kuzida | `1218-yil kuzi` | `1218` | `""` | `XIII` |
| XV asrda | `XV asr` | `1401` | `1500` | `XV` |
| XV asrning ikkinchi yarmida | `XV asrning ikkinchi yarmi` | `1451` | `1500` | `XV` |
| 1920-yillarda | `1920-yillar` | `1920` | `1929` | `XX` |
| miloddan avvalgi 329-yilda | `mil. avv. 329-yil` | `-329` | `""` | `IV` |
| mil. avv. VI–IV asrlarda | `mil. avv. VI–IV asrlar` | `-600` | `-301` | `VI–IV` |
| mil. avv. 3-mingyillikda | `mil. avv. 3-mingyillik` | `-3000` | `-2001` | `""` |

- Miloddan avvalgi yillar — **manfiy** son.
- Oraliqda `–` (uzun chiziq), `-yil`/`-yillar` oldidan `-` (defis).
- `sana_matn` darslikdagi aniqlikda: kun va oy berilgan bo‘lsa — yoz; berilmagan bo‘lsa — o‘ylab topma.
- `asr` rim raqamlarida va `yil_boshi` shu asrga to‘g‘ri kelsin (1370 → XIV; 1401 → XV; 1400 → XIV).
- Taxminiy sana ("taxminan 1220-yil") → `sana_matn`: `taxminan 1220-yil`, `ishonch`: `o‘rta`.

## 4-qoida: `sana` turiga xos talablar

1. **Bitta qator = bitta voqea + bitta sana.** "1370-yilda Temur taxtga o‘tirdi va Samarqandni poytaxt qildi" — ikkita alohida voqea bo‘lsa, ikkita qator. Ikki voqeani bitta sanaga qo‘shma.
2. Faqat **sanasi darslikda yozilgan** voqealar. Sanasiz voqeani yozma.
3. `nom` — voqeaning qisqa, aniq nomi, 3–9 so‘z, otlashgan shaklda:
   - ✅ `Amir Temurning Balxdagi qurultoyda hukmdor deb e’lon qilinishi`, `Buxoro amirligining tugatilishi`, `Dandanaqon jangi`
   - ❌ `1370-yilgi qurultoy` (nomda yil), `XV asrdagi islohotlar` (nomda asr), `Qurultoy` (juda umumiy), `Muhim voqea` (mazmunsiz)
   - Nomda **yil, asr, raqam bo‘lmasin**: savolda nom ko‘rsatiladi, sana so‘raladi — sana nomda bo‘lsa javob ko‘rinib qoladi.
   - Nom voqeani boshqalaridan aniq ajratsin: qayerda va kim bilan bog‘liqligi bo‘lsin (`Samarqanddagi qo‘zg‘olon` emas, `Sarbadorlarning Samarqanddagi qo‘zg‘oloni`).
4. `matn` — voqea, uning sanasi va natijasi yoki ahamiyati (1–2 gap). Sana matnda bo‘lishi mumkin.
5. Bir xil voqea darslikda bir necha marta tilga olinsa — bitta qator (eng to‘liq yozilgan joyidan).
6. `shaxs_*`, `urush_*`, `golib`, `natija`, `joy_*`, `asar_muallifi` — bo‘sh.
7. Urush va janglarni ham yozish mumkin, lekin ularning batafsil ma’lumoti (tomonlar, g‘olib) "urush" promptida alohida tuziladi.

## Namuna qator

```csv
"K07U-12-SAN01","sana","Amir Temurning Balxdagi qurultoyda hukmdor deb e’lon qilinishi","1370-yilda Balxda o‘tkazilgan qurultoyda Amir Temur Movarounnahrning oliy hukmdori deb e’lon qilindi.","1370-yil","1370","","XIV","O‘rta asrlar","O‘zbekiston va Markaziy Osiyo","7","K07U","12-§","Amir Temur davlatining tashkil topishi","85","1370-yil Balxda qurultoy chaqirilib, Amir Temur oliy hukmdor deb e’lon qilindi.","","","","","","","","","yuqori",""
```

## Chiqarishdan oldin o‘zingni tekshir

Har bir qatorni quyidagi ro‘yxat bo‘yicha tekshir. Qoidaga to‘g‘ri kelmagan qatorni tuzat yoki olib tashla:

- [ ] Har bir fakt darslik matnida bor; o‘zimdan hech narsa qo‘shmadim.
- [ ] `bet` va `iqtibos` aynan shu faktga tegishli; iqtibos so‘zma-so‘z.
- [ ] `matn` mustaqil, `Bu/U/Ushbu...` bilan boshlanmaydi.
- [ ] Sana, yil, asr bir-biriga mos; mil. avv. yillar manfiy.
- [ ] `o‘`, `g‘` faqat `‘` bilan; qiymatlar ichida `"` yo‘q; kirill harfi yo‘q.
- [ ] 26 ta ustun, har qatorda 26 ta qiymat, hammasi tirnoqda.
- [ ] `id` lar takrorlanmaydi; tegishli bo‘lmagan ustunlar bo‘sh.
- [ ] Har qatorda bitta voqea va bitta sana; ikki voqea bitta qatorga qo‘shilmagan.
- [ ] `nom` da yil, asr, raqam yo‘q; nom aniq va o‘ziga xos.

Endi kirish ma’lumotlarini kut. Ular kelgach — faqat CSV kod blokini chiqar.
````
