"""Faktlarni tekshirish (CLAUDE.md → "Mezon xatolarini takrorlamaslik").

Har qator uchun:
* matnlar tozalanadi (qo'sh qo'shtirnoq, o‘/g‘ uchun ‘ belgisi);
* muammolar `flags` ro'yxatiga yoziladi;
* jiddiy muammoda fakt foydalanuvchidan yashiriladi (`hidden=True`).

Bayroqlar va ularning ta'siri:
  ishonch_past           — yashiriladi (CLAUDE.md talabi)
  manba_yoq              — yashiriladi: har faktda darslik beti bo'lishi shart
  tur_nomalum            — yashiriladi
  matn_yoq               — yashiriladi
  yil_xato               — yil son emas; yil olib tashlanadi, o'yinlarga kirmaydi
  yil_yoq                — sana faktida aniq yil yo'q: kartochkada bor, yil o'yinlarida yo'q
  yil_asr_mos_emas       — yil va asr bir-biriga zid: yil o'yinlarida yo'q
  atama_ozini_tushuntiradi — ta'rif ichida atamaning o'zi bor: savolda atama yashirib ko'rsatiladi
  kontekstsiz            — "Bu...", "U..." bilan boshlanadi: matn yolg'iz ko'rsatiladigan o'yinlarda yo'q
  ishoralar_kam          — shaxsda 3 tadan kam ishora: "Kim men?" o'yinida yo'q
"""
import re
from dataclasses import dataclass, field

from app.models import FACT_TYPES

HIDE_FLAGS = {"ishonch_past", "manba_yoq", "tur_nomalum", "matn_yoq"}
NO_YEAR_GAME_FLAGS = {"yil_yoq", "yil_xato", "yil_asr_mos_emas"}

TEXT_FIELDS = ("nom", "matn", "sana_matn", "asr", "mavzu_nomi", "iqtibos", "golib", "natija",
               "joy_hozirgi", "asar_muallifi", "shaxs_faoliyati")
LIST_FIELDS = ("shaxs_ishoralar", "urush_tomonlari")

_ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}


def roman_to_int(s: str) -> int:
    total = 0
    for i, ch in enumerate(s):
        v = _ROMAN[ch]
        total += -v if i + 1 < len(s) and _ROMAN[s[i + 1]] > v else v
    return total


def century_of(year: int) -> int:
    """1336 -> 14, -329 -> 4 (mil. avv. IV asr)."""
    return (abs(year) - 1) // 100 + 1


def clean_text(text: str) -> str:
    """Bo'sh joylar, qo'sh qo'shtirnoq va o‘/g‘ belgisini to'g'rilaydi."""
    if not text:
        return ""
    t = " ".join(text.split())
    t = re.sub(r"«{2,}", "«", t)
    t = re.sub(r"»{2,}", "»", t)
    t = re.sub(r'"{2,}', '"', t)
    # o' g' O' G' (va ʻ ` ’ variantlari) -> o‘ g‘ (CLAUDE.md: o‘ va g‘ uchun ‘)
    t = re.sub(r"([oOgG])['ʻ`’]", r"\1‘", t)
    # qolgan oddiy ' -> ’ (tutuq belgisi: ma’no, fir’avn)
    t = re.sub(r"(?<=\w)'(?=\w)", "’", t)
    return t


def split_multi(value: str) -> list[str]:
    return [clean_text(x) for x in (value or "").split("||") if x.strip()]


def parse_year(value: str) -> tuple[int | None, bool]:
    """(yil, xato_bormi)."""
    v = (value or "").strip()
    if not v:
        return None, False
    try:
        return int(float(v)), False
    except ValueError:
        return None, True


def _norm_word(s: str) -> str:
    return re.sub(r"[«»\"“”‘’'ʻ`]", "", s).lower().strip()


@dataclass
class CheckedFact:
    data: dict
    flags: list[str] = field(default_factory=list)

    @property
    def hidden(self) -> bool:
        return bool(HIDE_FLAGS & set(self.flags))


def check_row(row: dict[str, str]) -> CheckedFact:
    """Bitta CSV qatorini tozalaydi va tekshiradi."""
    flags: list[str] = []
    d: dict = {"id": (row.get("id") or "").strip(), "tur": (row.get("tur") or "").strip()}
    for f in TEXT_FIELDS:
        d[f] = clean_text(row.get(f, ""))
    for f in LIST_FIELDS:
        d[f] = split_multi(row.get(f, ""))
    for f in ("davr", "hudud", "kitob_id", "paragraf", "bet", "joy_turi", "ishonch"):
        d[f] = clean_text(row.get(f, ""))
    d["izoh"] = (row.get("izoh") or "").strip()
    try:
        d["sinf"] = int(float(row.get("sinf") or 0))
    except ValueError:
        d["sinf"] = 0

    y1, bad1 = parse_year(row.get("yil_boshi", ""))
    y2, bad2 = parse_year(row.get("yil_oxiri", ""))
    d["yil_boshi"], d["yil_oxiri"] = y1, y2
    if bad1 or bad2:
        flags.append("yil_xato")

    if d["ishonch"] == "past":
        flags.append("ishonch_past")
    if d["tur"] not in FACT_TYPES:
        flags.append("tur_nomalum")
    if not d["nom"] or not d["matn"]:
        flags.append("matn_yoq")
    if not d["kitob_id"] or not d["bet"]:
        flags.append("manba_yoq")

    if d["tur"] == "sana" and y1 is None:
        flags.append("yil_yoq")
    if y1 is not None and d["asr"]:
        centuries = [roman_to_int(x) for x in re.findall(r"[IVXLC]+", d["asr"])]
        if centuries and not min(centuries) <= century_of(y1) <= max(centuries):
            flags.append("yil_asr_mos_emas")

    if d["tur"] == "atama":
        term = _norm_word(d["nom"])
        if len(term) > 3 and term in _norm_word(d["matn"]):
            flags.append("atama_ozini_tushuntiradi")
    if re.match(r"^(Bu|U|Ular|Shu|Ushbu)\b", d["matn"]):
        flags.append("kontekstsiz")
    if d["tur"] == "shaxs" and len(d["shaxs_ishoralar"]) < 3:
        flags.append("ishoralar_kam")

    return CheckedFact(d, flags)


def book_from_id(book_id: str) -> tuple[int, str] | None:
    """K08J -> (8, "Jahon tarixi"); K10U -> (10, "O‘zbekiston tarixi")."""
    m = re.fullmatch(r"K(\d{1,2})([JU])", book_id or "")
    if not m:
        return None
    return int(m.group(1)), "Jahon tarixi" if m.group(2) == "J" else "O‘zbekiston tarixi"
