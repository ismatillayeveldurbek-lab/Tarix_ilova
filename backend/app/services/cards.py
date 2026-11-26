"""Faktdan kartochka tuzish: old tomoni (savol) va orqa tomoni (javob).

Qoida (CLAUDE.md): javob klientga oldindan yuborilmaydi va savol matnida "sizib chiqmaydi".
Shuning uchun savolda javobni bildiradigan so'zlar "…" bilan yashiriladi:
  * sana nomida yil bo'lsa (masalan, "1991-yil Mustaqillik") — raqamlar yashiriladi;
  * joy, asar, atama tavsifida nomning o'zi bo'lsa — nom yashiriladi;
  * shaxs ishoralarida ism bo'lsa — ism yashiriladi.
"""
import re

from app.models import Fact

MASK = "…"
TYPE_LABELS = {"sana": "Yillar", "shaxs": "Shaxslar", "atama": "Atamalar", "joy": "Joylar",
               "urush": "Urushlar", "asar": "Asarlar"}
JOY_TURI = {"shahar": "Qaysi shahar?", "davlat": "Qaysi davlat?", "hudud": "Qaysi hudud?", "daryo": "Qaysi daryo?"}


def _terms(name: str) -> list[str]:
    """Yashiriladigan so'zlar: to'liq nom va undagi katta harfli uzun so'zlar (ism, joy nomi)."""
    clean = re.sub(r"[«»\"“”]", "", name).strip()
    words = [w.strip(".,;:()") for w in clean.split()]
    keys = [w for w in words if len(w) >= 4 and w[:1].isupper()]
    return sorted({clean, *keys}, key=len, reverse=True)


def mask(text: str, terms: list[str]) -> str:
    """Matndagi atamalarni (katta-kichik harfdan qat'i nazar, so'z qo'shimchalari bilan) yashiradi."""
    out = text
    for term in terms:
        if not term:
            continue
        # «Avesto», Avestoning, avesto — barchasi yashiriladi
        out = re.sub(r"«?" + re.escape(term) + r"»?[\w‘’]*", MASK, out, flags=re.IGNORECASE)
    return re.sub(r"(…\s*){2,}", "… ", out)


def mask_years(text: str) -> str:
    return re.sub(r"\d+", MASK, text)


def _leaks(answer: str, shown: str) -> bool:
    a = re.sub(r"[«»\"]", "", answer).lower().strip()
    return len(a) >= 3 and a in shown.lower()


RECALL = "Bu haqida nimani bilasiz?"


def _when(f: Fact) -> tuple[str, str]:
    """"Qachon?" savoli. Yil raqamlari yashiriladi; sana so'z bilan berilgan bo'lsa
    ("ilk paleolit oxirlari") va u nomda ko'rinib qolsa — bo'sh joyni to'ldirish savoli tuziladi.
    Sana umuman bo'lmasa yoki uni yashirib bo'lmasa — faol eslash kartasi (nom -> fakt)."""
    if not f.sana_matn and f.yil_boshi is None:
        return RECALL, f.nom
    body = mask_years(f.nom)
    if f.sana_matn and _leaks(f.sana_matn, body):
        cloze = mask_years(mask(f.matn, [f.sana_matn]))
        if MASK in cloze and not _leaks(f.sana_matn, cloze):
            return "Bo‘sh joyni to‘ldiring", cloze
        return RECALL, f.nom
    return "Bu qachon bo‘lgan?", body


def front(f: Fact) -> dict:
    """Kartaning old tomoni. JAVOB BU YERGA KIRMAYDI."""
    prompt, body, hints = "", "", []
    if f.tur == "sana":
        prompt, body = _when(f)
    elif f.tur == "shaxs":
        prompt = "Kim haqida gap ketmoqda?"
        terms = _terms(f.nom)
        if len(f.shaxs_ishoralar) >= 2:
            hints = [mask(h, terms) for h in f.shaxs_ishoralar]
        else:
            body = mask(f.matn, terms)
    elif f.tur == "atama":
        prompt = "Qaysi atama?"
        body = mask(f.matn, _terms(f.nom))
    elif f.tur == "asar":
        if f.asar_muallifi:
            prompt = "Muallifi kim?"
            body = mask(f.nom, _terms(f.asar_muallifi))  # «Tarix» (Gerodot) -> «Tarix» (…)
        else:
            prompt = "Qaysi asar?"
            body = mask(f.matn, _terms(f.nom))
    elif f.tur == "urush":
        # Nom ko'pincha g'olibni aytib qo'yadi ("Forslarning Misrni bosib olishi") —
        # shuning uchun yili bor bo'lsa "Qachon?" so'raladi, g'olib va natija javobda ko'rsatiladi
        if f.sana_matn:
            prompt, body = _when(f)
        elif f.golib and not _leaks(f.golib, f.nom):
            prompt = "Kim g‘olib bo‘lgan?"
            body = f.nom
            hints = [" — ".join(f.urush_tomonlari)] if f.urush_tomonlari else []
        else:
            prompt = "Natijasi qanday bo‘lgan?"
            body = f.nom
    elif f.tur == "joy":
        prompt = JOY_TURI.get(f.joy_turi, "Qaysi joy?")
        body = mask(f.matn, _terms(f.nom))
    else:
        prompt, body = "Eslang", f.nom
    return {
        "fact_id": f.id, "tur": f.tur, "label": TYPE_LABELS.get(f.tur, f.tur),
        "prompt": prompt, "body": body, "hints": hints, "davr": f.davr, "sinf": f.sinf,
    }


def back(f: Fact) -> dict:
    """Kartaning orqa tomoni: javob, to'liq fakt va darslik manbasi."""
    prompt = front(f)["prompt"]  # javob savol turiga mos bo'lishi shart
    if prompt in ("Bu qachon bo‘lgan?", "Bo‘sh joyni to‘ldiring"):
        answer = f.sana_matn or (str(f.yil_boshi) if f.yil_boshi is not None else "")
    elif prompt == "Muallifi kim?":
        answer = f.asar_muallifi
    elif prompt == "Kim g‘olib bo‘lgan?":
        answer = f.golib
    elif prompt == "Natijasi qanday bo‘lgan?":
        answer = f.natija or f.matn
    elif prompt == RECALL:
        answer = f.matn
    else:
        answer = f.nom
    extra = []
    if f.tur == "joy" and f.joy_hozirgi:
        extra.append(f"Hozirgi joyi: {f.joy_hozirgi}")
    if f.tur == "urush":
        if f.urush_tomonlari:
            extra.append("Tomonlar: " + " — ".join(f.urush_tomonlari))
        if f.golib and f.sana_matn:
            extra.append(f"G‘olib: {f.golib}")
        if f.natija and answer != f.natija:
            extra.append(f"Natija: {f.natija}")
    if f.tur == "shaxs" and f.shaxs_faoliyati:
        extra.append(f"Faoliyati: {f.shaxs_faoliyati}")
    return {
        "fact_id": f.id, "answer": answer, "title": f.nom, "text": f.matn, "extra": extra,
        "sana": f.sana_matn, "source": f.source, "mavzu": f.mavzu_nomi, "iqtibos": f.iqtibos,
    }


def card_ok(f: Fact) -> bool:
    """Kartadan foydalansa bo'ladimi: old tomoni bo'sh emas va javob savolda ko'rinmaydi.
    ("Kim g'olib?" savolida tomonlar variant sifatida ko'rsatiladi — bu sizish emas.)"""
    fr = front(f)
    if not (fr["body"].strip(" …") or fr["hints"]):
        return False
    answer = back(f)["answer"]
    if not answer:
        return False
    if fr["prompt"] == RECALL:
        return f.nom.strip() != f.matn.strip()
    shown = fr["body"] + (" " + " ".join(fr["hints"]) if fr["prompt"] != "Kim g‘olib bo‘lgan?" else "")
    return not _leaks(answer, shown)
