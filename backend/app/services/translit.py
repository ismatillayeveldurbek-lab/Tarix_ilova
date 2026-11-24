"""O'zbek lotin yozuvidan kirill yozuviga o'girish.

Barcha matnlar bazada LOTINDA saqlanadi. Foydalanuvchi kirillni tanlasa,
ko'rsatishdan oldin shu funksiya orqali o'giriladi.
HTML teglari (<b>), &amp; kabi belgilar va {o'zgaruvchilar} o'girilmaydi.
"""
import re

APOSTROPHES = "'ʻʼ‘’`"

SINGLE = {
    "a": "а", "b": "б", "d": "д", "e": "е", "f": "ф", "g": "г", "h": "ҳ", "i": "и",
    "j": "ж", "k": "к", "l": "л", "m": "м", "n": "н", "o": "о", "p": "п", "q": "қ",
    "r": "р", "s": "с", "t": "т", "u": "у", "v": "в", "x": "х", "y": "й", "z": "з",
    "c": "ц", "w": "в",
}
# y + unli -> bitta kirill harf
Y_VOWELS = {"o": "ё", "u": "ю", "a": "я", "e": "е"}
VOWELS = set("aeiouAEIOU")

# O'girilmaydigan bo'laklar: HTML teglari, &amp; belgilari, {o'zgaruvchilar}, havolalar, XP
# va rim raqamlari (XIV asr, Pyotr I, Kir II) — tarix matnlarida juda ko'p uchraydi
_SKIP = re.compile(r"(<[^>]+>|&#?\w+;|\{[^}]*\}|https?://\S+|\bXP\b|\b[IVXLCDM]+\b)")


def _case(src: str, cyr: str) -> str:
    """Asl harf katta bo'lsa, kirillni ham katta qiladi."""
    return cyr.upper() if src[:1].isupper() else cyr


def _is_apo(ch: str) -> bool:
    return ch != "" and ch in APOSTROPHES


def _convert(text: str) -> str:
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        low = ch.lower()
        nxt = text[i + 1] if i + 1 < n else ""
        nxt2 = text[i + 2] if i + 2 < n else ""

        # o' va g'
        if low in ("o", "g") and _is_apo(nxt):
            out.append(_case(ch, "ў" if low == "o" else "ғ"))
            i += 2
            continue
        # sh, ch
        if low in ("s", "c") and nxt.lower() == "h":
            out.append(_case(ch, "ш" if low == "s" else "ч"))
            i += 2
            continue
        # yo, yu, ya, ye (lekin "yo'" = й + ў)
        if low == "y" and nxt.lower() in Y_VOWELS and not (nxt.lower() == "o" and _is_apo(nxt2)):
            out.append(_case(ch, Y_VOWELS[nxt.lower()]))
            i += 2
            continue
        # e: so'z boshida yoki unlidan keyin -> э
        if low == "e":
            prev = text[i - 1] if i > 0 else ""
            at_start = not prev.isalpha() and not _is_apo(prev)
            out.append(_case(ch, "э" if at_start or prev in VOWELS else "е"))
            i += 1
            continue
        # tutuq belgisi (ma'no -> маъно)
        if _is_apo(ch) and i > 0 and text[i - 1].isalpha():
            out.append("ъ")
            i += 1
            continue
        if low in SINGLE:
            out.append(_case(ch, SINGLE[low]))
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def to_cyrillic(text: str) -> str:
    if not text:
        return text
    parts = _SKIP.split(text)
    # split natijasida toq indekslar — o'girilmaydigan bo'laklar
    return "".join(p if idx % 2 else _convert(p) for idx, p in enumerate(parts))


def tr(text: str, alphabet: str) -> str:
    """Foydalanuvchi alifbosiga moslab qaytaradi."""
    return to_cyrillic(text) if alphabet == "cyrl" else text
