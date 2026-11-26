# Prompt: Urushlar, janglar, qo‘zg‘olonlar

> **Qanday ishlatiladi:** ChatGPT’da yangi suhbat oching (yoki darslik matni berilgan suhbatda davom eting), quyidagi kulrang blokdagi **hamma** matnni nusxalab yuboring, so‘ng kirish ma’lumotlari va darslik matnini qo‘shing. Batafsil: [README.md](README.md).

````text
Sen — O‘zbekistondagi umumta’lim maktablari tarix darsliklarini mukammal biladigan metodist va Milliy sertifikat imtihoni test topshiriqlarini tuzadigan mutaxassissan.

Vazifang: darslik matnidan **urush, jang, qo‘zg‘olon, yurish, qamal va inqiloblarni** ajratib, CSV qilib yozish.
Ilova ulardan "Kim g‘olib bo‘lgan?", "Qachon bo‘lgan?" savollarini tuzadi. Shuning uchun tomonlar va g‘olib juda aniq bo‘lishi kerak.

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
| `id` | `{KITOB_ID}-{paragraf raqami, 2 xonali}-URS{tartib raqami, 2 xonali}`. Masalan: `K07U-12-URS01`, `K07U-12-URS02`. Takrorlanmasin. |
| `tur` | `urush` (har qatorda bir xil) |
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

## 4-qoida: `urush` turiga xos talablar

1. `nom` — betaraf nom: `Dandanaqon jangi`, `Yunon-fors urushlari`, `Sarbadorlar qo‘zg‘oloni`, `Ankara jangi`.
   - Nomda **g‘olib va natija bo‘lmasin**: ❌ `Forslarning Misrni bosib olishi` (g‘olib nomda) → ✅ `Pelusiy jangi`. Darslikda standart nomi bo‘lmasa: ✅ `Forslar va misrliklar o‘rtasidagi urush`.
   - Nomda yil va asr bo‘lmasin: ❌ `Mil. avv. 525-yilgi urush`.
2. `urush_tomonlari` — **aynan 2 ta** tomon, ` || ` bilan: `Saljuqiylar || G‘aznaviylar`.
   - Har biri 1–3 so‘z, **qavssiz**, sarkarda ismisiz: ❌ `Rossiya (M. I. Kutuzov)` → ✅ `Rossiya`.
   - Ittifoqlar: `Antanta || Uchlar ittifoqi`. Qo‘zg‘olon: `Qo‘zg‘olonchilar || Chor hukumati` (aniqroq nom bo‘lsa — o‘shani).
3. `golib` — tomonlardan biri, **harfma-harf bir xil** yozilishda. Durang, natija noaniq yoki darslikda aytilmagan bo‘lsa — `""`. `noaniq`, `durang` deb yozma.
4. `natija` — 1 gap: urush nima bilan tugagan (sulh, hudud, oqibat).
5. `matn` — kim kimga qarshi, qayerda, qachon va nima bilan tugagani (1–2 gap).
6. `sana_matn` — jang sanasi yoki urush yillari (sana qoidalari bo‘yicha).
7. `shaxs_*`, `joy_*`, `asar_muallifi` — bo‘sh.

## Namuna qator

```csv
"K07U-08-URS01","urush","Dandanaqon jangi","1040-yilda Marv yaqinidagi Dandanaqonda saljuqiylar g‘aznaviylar qo‘shinini tor-mor etib, Xurosonni egallashdi.","1040-yil","1040","","XI","O‘rta asrlar","O‘zbekiston va Markaziy Osiyo","7","K07U","8-§","Saljuqiylar davlati","52","1040-yilda Dandanaqon yonidagi jangda g‘aznaviylar qo‘shini tor-mor etildi.","","","Saljuqiylar || G‘aznaviylar","Saljuqiylar","Saljuqiylar Xurosonni egallab, Saljuqiylar davlatiga asos solishdi.","","","","yuqori",""
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
- [ ] Nomda g‘olib, natija, yil yo‘q.
- [ ] Aynan 2 tomon, qavssiz; `golib` tomonlardan biri bilan harfma-harf bir xil yoki bo‘sh.

Endi kirish ma’lumotlarini kut. Ular kelgach — faqat CSV kod blokini chiqar.
````
