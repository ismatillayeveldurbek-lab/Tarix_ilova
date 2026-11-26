# ChatGPT bilan faktlar bazasi va testlarni tayyorlash

Bu papkadagi promptlar ChatGPT’ga darslik matnidan **ilovaga to‘g‘ridan-to‘g‘ri yuklanadigan** CSV fayllar tayyorlatadi.
Har bir prompt ilovaning qoidalarini o‘z ichiga oladi (CLAUDE.md → "Mezon xatolarini takrorlamaslik").

| Fayl | Nima tayyorlaydi | Natija |
|---|---|---|
| [01-sana.md](01-sana.md) | Voqealar va sanalari | faktlar CSV (26 ustun) |
| [02-shaxs.md](02-shaxs.md) | Shaxslar + "Kim men?" ishoralari | faktlar CSV |
| [03-atama.md](03-atama.md) | Atamalar va ta’riflari | faktlar CSV |
| [04-joy.md](04-joy.md) | Shahar, davlat, hudud, daryo... | faktlar CSV |
| [05-urush.md](05-urush.md) | Urush, jang, qo‘zg‘olon: tomonlar, g‘olib | faktlar CSV |
| [06-asar.md](06-asar.md) | Yozma va me’moriy asarlar, mualliflar | faktlar CSV |
| [07-mavzu-testlari.md](07-mavzu-testlari.md) | Har mavzudan 15 ta test (4 variant) | testlar CSV (12 ustun) |
| [08-tekshiruvchi.md](08-tekshiruvchi.md) | Natijani darslik bilan solishtirib tuzatadi | tuzatilgan CSV |

## Ish tartibi (bitta paragraf uchun)

1. **Matnni tayyorlang.** Darslikning bitta paragrafini (§) PDF’dan nusxalang. Har bet boshiga `[bet 85]` kabi belgi qo‘ying — ChatGPT bet raqamini shundan oladi. PDF’ni to‘g‘ridan-to‘g‘ri yuklash mumkin, lekin matn bilan xato kamroq bo‘ladi.
2. **Yangi suhbat** oching. Eng kuchli, "fikrlaydigan" (reasoning) modelni tanlang.
3. Birinchi xabarda: kerakli promptni (masalan, `01-sana.md` dagi kulrang blok) + pastiga kirish ma’lumotlari:
   ```
   KITOB_ID: K07U
   SINF: 7
   FAN: O‘zbekiston tarixi
   PARAGRAF: 12-§
   MAVZU_NOMI: Amir Temur davlatining tashkil topishi
   DARSLIK MATNI:
   [bet 85] ...
   ```
4. Shu suhbatda keyingi promptlarni yuboring (`02-shaxs.md`, `03-atama.md`...). Darslik matnini qayta yuborish shart emas — har prompt "matn oldinroq berilgan bo‘lsa — o‘shani ishlat" deydi.
5. Har natijani **yangi suhbatda** `08-tekshiruvchi.md` bilan tekshiring.
6. Tuzatilgan CSV’ni faylga saqlang.

**Darslik kodlari:** `K` + sinf + `J` (Jahon tarixi) yoki `U` (O‘zbekiston tarixi): `K06J`, `K07J`, `K07U`, `K08J`, `K08U` ... `K11U`.

## Fayllarni nomlash va menga yuborish

- Faktlar: `K07U_12_sana.csv`, `K07U_12_shaxs.csv` ... (darslik, paragraf, tur).
- Testlar: `K07U_12_testlar.csv`.
- Bir darslikni tugatgach, fayllarni papka yoki ZIP qilib shu chatga yuboring. Men:
  1. hammasini bitta `data/baza.csv` ga birlashtiraman;
  2. import tekshiruvidan o‘tkazaman (format, takroriy ID, sana–asr mosligi, javob sizishi);
  3. xatolar ro‘yxatini qaytaraman;
  4. ilovaga yuklayman. Faktlardan avtomatik savollar ham, sizning mavzu testlaringiz ham ishlaydi.

Testlarni admin panel → **Import** orqali o‘zingiz ham yuklashingiz mumkin. Faktlarni esa admin panel → **Faktlar bazasi** → yuklash orqali.

## Muhim

- ChatGPT eng yaxshi promptda ham adashishi mumkin: ayniqsa **bet raqami, sanalar va ism yozilishida**. Shuning uchun 5-qadam (tekshiruvchi) majburiy.
- Darslikda xato yoki boshqa manbalarga zid joy bo‘lsa, ChatGPT uni `izoh` ga yozadi — shu qatorlarni o‘zingiz ko‘rib chiqing.
- Promptlardagi namuna qatorlar (bet raqami, iqtibos) faqat **formatni ko‘rsatish uchun**. ChatGPT ularni emas, sizning darslik matningizni ishlatadi.
- Tayyor faktlar faylini yuklashdan oldin tekshirib ko‘rish mumkin (bazaga yozmaydi): `python -m scripts.import_facts fayl.csv --dry-run`.
- Bir shaxs, asar yoki joy **hamma fayllarda bir xil yozilsin** (`Amir Temur`, bir joyda `Temur`, boshqasida `Temurbek` emas). Aks holda o‘yin va testlarda u ikki xil odam bo‘lib qoladi.
