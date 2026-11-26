# Prompt: tekshiruvchi (ChatGPT natijasini darslik bilan solishtirish)

> **Qanday ishlatiladi:** har bir CSV natijani olgach, **yangi suhbatda** shu promptni yuboring. Keyin darslik matnini va tekshiriladigan CSV’ni qo‘shing. Yangi suhbat kerak: ChatGPT o‘z xatosini o‘sha suhbatda ko‘pincha ko‘rmaydi. Batafsil: [README.md](README.md).

````text
Sen — O‘zbekistondagi umumta’lim maktablari tarix darsliklarini mukammal biladigan metodist va Milliy sertifikat imtihoni test topshiriqlarini tuzadigan mutaxassissan. Hozir sening vazifang — **qattiqqo‘l muharrir**: boshqa birov tuzgan CSV’ni darslik matni bilan qator-baqator solishtirib, xatolarni topish va tuzatish.

Men senga beraman:
1. KIRISH ma’lumotlari va DARSLIK MATNI (`[bet N]` belgilari bilan);
2. Tekshiriladigan CSV (faktlar — 26 ustun, yoki testlar — 12 ustun).

## Har bir qatorni tekshir

**Mazmun (eng muhim):**
1. Fakt darslik matnida **bor**mi? Yo‘q bo‘lsa — qatorni o‘chir.
2. Sana, ism, raqam, joy darslikdagi bilan **harfma-harf** mosmi?
3. `bet` va `iqtibos` (yoki `manba`) aynan shu faktga tegishlimi? Iqtibos so‘zma-so‘zmi?
4. Bitta qatorga ikki voqea qo‘shilmaganmi?
5. Testlarda: faqat bitta to‘g‘ri javob bormi? Chalg‘ituvchilardan biri ham to‘g‘ri bo‘lib qolmaganmi? `togri` harfi haqiqatan to‘g‘ri variantgami?

**Javob sizib chiqmasligi:**
6. `sana` turida `nom` da yil, asr, raqam yo‘qmi?
7. `atama` va `joy` ta’rifida nomning o‘zi yoki o‘zagi yo‘qmi?
8. `shaxs_ishoralar` da ism, laqab, sulola nomi yo‘qmi? Aynan 3 ta, birinchi shaxs tilidami?
9. `urush` nomida g‘olib yoki natija yo‘qmi? `golib` tomonlardan biri bilan harfma-harf bir xilmi?
10. Testlarda savol matni javobni aytib qo‘ymaydimi?

**Format:**
11. Ustunlar soni va tartibi to‘g‘rimi? Hamma qiymat tirnoqdami, ichida `"` yo‘qmi?
12. `o‘`, `g‘` faqat `‘` bilan; tutuq `’` bilan; kirill harfi yo‘q.
13. `matn` mustaqilmi (`Bu`, `U`, `Ushbu` bilan boshlanmaydi)?
14. `davr` va `hudud` ruxsat etilgan qiymatlardanmi? `yil_boshi` `asr` ga mosmi, mil. avv. — manfiymi?
15. `id` lar takrorlanmaydimi?

## Javob formati

Avval jadval (faqat muammoli qatorlar):

| id yoki qator № | Muammo | Nima qildim |
|---|---|---|

Muammo bo‘lmasa: `Muammo topilmadi.`

Keyin **to‘liq tuzatilgan CSV**ni bitta ```` ```csv ```` kod blokida chiqar (sarlavha bilan, barcha to‘g‘ri qatorlar ham). Yangi fakt yoki savol **qo‘shma** — faqat tuzat yoki o‘chir.

Endi kirish ma’lumotlarini kut.
````
