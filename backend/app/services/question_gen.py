"""Faktlar bazasidan 4 variantli test savollarini tuzish.

Har savol bitta faktdan va bitta "tur"dan tuziladi (gen_key = "K07J-0012:qachon"):

  qachon  — sana/urush: "… qachon bo‘lgan?"   variantlar: o‘sha shakldagi boshqa sanalar
  kim     — shaxs: "Kim men?" + ishoralar      variantlar: o‘sha davr va kasbdagi shaxslar
  atama   — ta’rif -> atama                     variantlar: o‘sha davr atamalari
  joy     — tavsif -> joy                       variantlar: o‘sha turdagi joylar
  muallif — asar -> muallif                     variantlar: boshqa mualliflar, olim va shoirlar
  asar    — tavsif -> asar                      variantlar: boshqa asarlar
  golib   — urush -> g‘olib                     variantlar: tomonlar va boshqa g‘oliblar

Qoidalar (CLAUDE.md → "Mezon xatolarini takrorlamaslik"):
  * javob savol matnida ko‘rinmaydi (nom va yillar yashiriladi, sizsa — savol tuzilmaydi);
  * chalg‘ituvchi variantlar o‘sha tur va davrdan, bema’ni emas;
  * sana variantlari bir xil shaklda ("1370-yil" yonida "XV asr" turmaydi) va oraliqlari kesishmaydi;
  * vaqt savolida davr va mavzu javobdan oldin ko‘rsatilmaydi (asks_time);
  * kontekstsiz matnlar va tahrir izohi tushgan faktlar ishlatilmaydi;
  * izohda doim darslik manbasi bor.
Natija barqaror: bir xil baza — bir xil savollar (tasodif fakt ID’sidan olinadi).
"""
import random
import re
import zlib
from collections import defaultdict
from dataclasses import dataclass, field

from app.models import Fact
from app.services.cards import _leaks, _terms, mask
from app.services.game_oldin import interval

DAVR_TO_PERIOD = {"Qadimgi": "Qadimgi davr", "O‘rta asrlar": "O‘rta asrlar", "Yangi": "Yangi davr", "Eng yangi": "Eng yangi davr"}
PERIOD_ORDER = list(DAVR_TO_PERIOD.values())
JOY_PROMPT = {"shahar": "Qaysi shahar haqida gap ketmoqda?", "davlat": "Qaysi davlat haqida gap ketmoqda?",
              "hudud": "Qaysi hudud haqida gap ketmoqda?", "daryo": "Qaysi daryo haqida gap ketmoqda?",
              "qal’a": "Qaysi qal’a haqida gap ketmoqda?"}
AUTHOR_JOBS = {"olim", "shoir", "yozuvchi", "tarixchi", "faylasuf", "sayyoh"}
SKIP_FLAGS = {"maydonda_izoh"}
TEXT_SKIP_FLAGS = {"kontekstsiz"}  # matn yolg‘iz ko‘rsatiladigan savollarda ishlatilmaydi
MONTHS = ("yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul", "avgust", "sentabr", "sentyabr",
          "oktabr", "oktyabr", "noyabr", "dekabr")


@dataclass
class GenQuestion:
    key: str
    fact: Fact
    kind: str
    text: str
    options: list[str]          # 4 ta, aralashtirilgan
    correct: str                # "a".."d"
    explanation: str
    difficulty: int
    asks_time: bool = False
    extra: dict = field(default_factory=dict)


def _rng(key: str) -> random.Random:
    return random.Random(zlib.crc32(key.encode()))


def _norm(s: str) -> str:
    return re.sub(r"[«»\"“”()‘’'ʻ`.,]", "", s).lower().strip()


def _clash(a: str, b: str) -> bool:
    """Ikki variant bir-biriga juda o‘xshash: biri ikkinchisining ichida ("Bobur" / "Zahiriddin Muhammad Bobur")."""
    x, y = _norm(a), _norm(b)
    return not x or not y or x == y or x in y or y in x


def _pick(correct: str, pools: list[list[str]], rng: random.Random, n: int = 3) -> list[str] | None:
    """Afzal havzadan boshlab n ta chalg‘ituvchi variant tanlaydi."""
    chosen: list[str] = []
    for pool in pools:
        cands = list(dict.fromkeys(pool))
        rng.shuffle(cands)
        for c in cands:
            if len(chosen) == n:
                break
            if c and not _clash(c, correct) and not any(_clash(c, x) for x in chosen):
                chosen.append(c)
    return chosen if len(chosen) == n else None


def _assemble(key: str, f: Fact, kind: str, text: str, correct: str, distractors: list[str],
              difficulty: int, asks_time: bool = False) -> GenQuestion:
    rng = _rng(key + ":tartib")
    opts = distractors + [correct]
    rng.shuffle(opts)
    letter = "abcd"[opts.index(correct)]
    expl = f.matn
    if f.source:
        expl += f"\n\nManba: {f.source}"
    return GenQuestion(key, f, kind, text, opts, letter, expl, difficulty, asks_time)


# ---------- Sanalar ----------

def date_shape(s: str) -> str | None:
    """Sana matnining shakli: variantlar bir xil shaklda bo‘lishi kerak."""
    t = s.lower().strip()
    if not t:
        return None
    if "mingyillik" in t:
        return "ming"
    if "asr" in t:
        return "asr" if re.fullmatch(r"(mil\. avv\. )?[ivxlc]+ asr", t) else "asr_qism"
    if any(m in t for m in MONTHS):
        return "kun"
    if re.fullmatch(r"(mil\. avv\. )?\d{1,4}-yil", t):
        return "yil"
    if re.fullmatch(r"(mil\. avv\. )?\d{1,4}[–-]\d{1,4}-yillar", t):
        return "oraliq"
    if re.fullmatch(r"\d{3,4}-yillar", t):
        return "onyillik"
    return None


def _gap_ok(a: tuple[int, int], b: tuple[int, int], shape: str) -> bool:
    """Oraliqlar kesishmaydi va bir-biridan yetarlicha uzoq (aks holda savol bahsli)."""
    min_gap = {"yil": 3, "kun": 3, "oraliq": 2, "onyillik": 10, "asr": 1, "asr_qism": 10, "ming": 1}[shape]
    return a[1] + min_gap <= b[0] or b[1] + min_gap <= a[0]


def _when_q(f: Fact, by_shape: dict, kind_key: str) -> GenQuestion | None:
    # Nomda yil yoki asr bo'lsa ("Inklarning XV asrdagi istilolari") — javob ko'rinib qoladi
    if not f.sana_matn or re.search(r"\d|\b[IVXLC]+\s+asr|\basr|ming\s*yil", f.nom) or _leaks(f.sana_matn, f.nom):
        return None
    shape, iv = date_shape(f.sana_matn), interval(f)
    if shape is None or iv is None:
        return None
    key = f"{f.id}:{kind_key}"
    rng = _rng(key)
    same_davr, other = [], []
    for g, giv in by_shape.get(shape, []):
        if g.id != f.id and _gap_ok(iv, giv, shape):
            (same_davr if g.davr == f.davr else other).append((g, giv))
    # Eng yaqin sanalardan tanlanadi: 484-yil yonida 1216, 1263, 1370 tursa — javob "yagona eski" bo'lib qoladi
    mid = (iv[0] + iv[1]) / 2
    near = sorted(same_davr + other, key=lambda x: (abs((x[1][0] + x[1][1]) / 2 - mid), x[0].id))[:10]
    rng.shuffle(near)
    chosen: list[tuple[str, tuple[int, int]]] = []
    for g, giv in near + sorted(same_davr + other, key=lambda x: x[0].id):
        if len(chosen) == 3:
            break
        if all(_gap_ok(giv, c[1], shape) and _norm(g.sana_matn) != _norm(c[0]) for c in chosen):
            chosen.append((g.sana_matn, giv))
    if len(chosen) < 3:
        return None
    difficulty = {"asr": 1, "ming": 1, "onyillik": 2, "oraliq": 2, "asr_qism": 2, "yil": 3, "kun": 3}[shape]
    text = f"Bu qaysi sanaga to‘g‘ri keladi?\n{f.nom}"
    return _assemble(key, f, "qachon", text, f.sana_matn, [c[0] for c in chosen], difficulty, asks_time=True)


# ---------- Shaxs, atama, joy, asar, urush ----------

def _text_ok(f: Fact) -> bool:
    return not (TEXT_SKIP_FLAGS & set(f.flags or []))


def _described(f: Fact) -> str | None:
    """Faktning tavsifi, nomi yashirilgan. Nom sizsa yoki tavsif bo‘sh qolsa — None."""
    if not _text_ok(f):
        return None
    body = mask(f.matn, _terms(f.nom))
    body = re.sub(r"^…\s*([—–-]\s*)?", "", body).strip()  # "Sug‘diyona — yunon manbalarida..." -> "Yunon..."
    body = body[:1].upper() + body[1:]
    if len(body.replace("…", "").strip()) < 25 or body.count("…") > 2 or _leaks(f.nom, body):
        return None
    return body


def _who_q(f: Fact, pools: dict) -> GenQuestion | None:
    terms = _terms(f.nom)
    hints = [mask(h, terms) for h in f.shaxs_ishoralar[:3]]
    if len(hints) >= 2 and not any(_leaks(f.nom, h) for h in hints):
        text = "Kim men?\n" + "\n".join(f"— {h}" for h in hints)
    else:
        body = _described(f)
        if body is None:
            return None
        text = f"Kim haqida gap ketmoqda?\n{body}"
    key = f"{f.id}:kim"
    d = _pick(f.nom, [pools["shaxs", f.davr, f"{f.shaxs_faoliyati}|{f.hudud}"], pools["shaxs", f.davr, f.shaxs_faoliyati],
                      pools["shaxs", f.davr, f.hudud], pools["shaxs", f.davr, ""]], _rng(key))
    if not d:
        return None
    return _assemble(key, f, "kim", text, f.nom, d, 2 if f.shaxs_faoliyati in ("hukmdor", "siyosatchi") else 1)


def _term_q(f: Fact, pools: dict) -> GenQuestion | None:
    body = _described(f)
    if body is None:
        return None
    key = f"{f.id}:atama"
    d = _pick(f.nom, [pools["atama", f.davr, f.hudud], pools["atama", f.davr, ""]], _rng(key))
    if not d:
        return None
    return _assemble(key, f, "atama", f"Qaysi atama shunday ta’riflanadi?\n{body}", f.nom, d, 2)


def _place_q(f: Fact, pools: dict) -> GenQuestion | None:
    if f.joy_turi in ("boshqa", ""):  # kanal, maktab, kompaniya aralash — variantlar bema'ni bo'lib qoladi
        return None
    body = _described(f)
    if body is None:
        return None
    key = f"{f.id}:joy"
    d = _pick(f.nom, [pools["joy", f.davr, f"{f.joy_turi}|{f.hudud}"], pools["joy", "", f"{f.joy_turi}|{f.hudud}"],
                      pools["joy", f.davr, f.hudud], pools["joy", f.davr, f.joy_turi], pools["joy", f.davr, ""]], _rng(key))
    if not d:
        return None
    return _assemble(key, f, "joy", f"{JOY_PROMPT.get(f.joy_turi, 'Qaysi joy haqida gap ketmoqda?')}\n{body}", f.nom, d, 2)


def _author_q(f: Fact, pools: dict) -> GenQuestion | None:
    author = f.asar_muallifi
    # «Tarix» (Gerodot) -> «Tarix»: qavsdagi muallif olib tashlanadi
    title = re.sub(r"\s*\([^)]*\)", "", f.nom).strip() if _leaks(author, f.nom) else f.nom
    if not title or _leaks(author, title) or len(author) > 60:
        return None
    key = f"{f.id}:muallif"
    d = _pick(author, [pools["muallif", f.davr, f.hudud], pools["muallif", f.davr, ""], pools["muallif", "", ""]], _rng(key))
    if not d:
        return None
    return _assemble(key, f, "muallif", f"{title} asarining muallifi kim?", author, d, 2)


BUILDING = re.compile(r"madrasa|masjid|minora|maqbara|saroy|qasr|ibodatxona|bazilika|cherkov|ma’bad|haykal|inshoot|"
                      r"qal’a|sobor|piramida|darvoza|qurilgan|qurdirgan|bunyod|me’moriy|majmua|xonaqoh|rasadxona|hammom|ko‘prik",
                      re.IGNORECASE)


def is_building(f: Fact) -> bool:
    return not work_title(f.nom).startswith("«") and bool(BUILDING.search(f.nom + " " + f.matn))


def work_title(nom: str) -> str:
    """«Buyuk Temur tarixi» (Pero Meksika) -> «Buyuk Temur tarixi»"""
    return re.sub(r"\s*\([^)]*\)\s*$", "", nom).strip() or nom


def _work_q(f: Fact, pools: dict) -> GenQuestion | None:
    body = _described(f)
    if body is None:
        return None
    key = f"{f.id}:asar"
    title = work_title(f.nom)
    kind = "bino" if is_building(f) else "kitob"  # kitob yoki inshoot — variantlar bir xil turdan
    d = _pick(title, [pools["asar", f.davr, f"{kind}|{f.hudud}"], pools["asar", f.davr, kind], pools["asar", "", kind]], _rng(key))
    if not d:
        return None
    what = "yodgorlik" if kind == "bino" else "asar"
    return _assemble(key, f, "asar", f"Qaysi {what} haqida gap ketmoqda?\n{body}", title, d, 2)


def clean_side(s: str) -> str:
    """"Rossiya (M. I. Kutuzov)" -> "Rossiya"; aniq bo'lmagan qiymat ("noaniq", "durang") -> "" """
    s = re.sub(r"\s*\([^)]*\)", "", s).strip()
    if not s or _norm(s) in {"noaniq", "durang", "durrang", "hech kim", "yo‘q"} or len(s.split()) > 3 or "«" in s:
        return ""
    return s


def _words(s: str) -> set[str]:
    return {w for w in re.findall(r"\w+", _norm(s)) if len(w) >= 5}


def _winner_q(f: Fact, pools: dict) -> GenQuestion | None:
    """Faqat aniq g'olib (davlat yoki xalq nomi) bo'lsa. Variantlarda g'olibga o'xshash
    nomlar ("Sovet hokimiyati" / "Sovet qo'shinlari") bo'lmaydi — aks holda savol bahsli."""
    golib = clean_side(f.golib)
    if not golib or _leaks(golib, f.nom) or _words(golib) & _words(f.nom):  # "Niderland inqilobi" -> "Niderland xalqi"
        return None
    sides = [clean_side(s) for s in f.urush_tomonlari]
    if not any(_clash(s, golib) for s in sides if s):  # g'olib tomonlardan biri bo'lishi shart
        return None
    distinct = lambda pool: [x for x in pool if x and not (_words(x) & _words(golib))]  # noqa: E731
    key = f"{f.id}:golib"
    d = _pick(golib, [distinct([s for s in sides if not _clash(s, golib)]),
                      distinct(pools["golib", f.davr, f.hudud]), distinct(pools["golib", f.davr, ""])], _rng(key))
    if not d:
        return None
    return _assemble(key, f, "golib", f"{f.nom}: kim g‘olib bo‘lgan?", golib, d, 2)


def _pools(facts: list[Fact]) -> dict:
    """Chalg‘ituvchi variantlar havzalari: (tur, davr, qo‘shimcha belgi) -> qiymatlar."""
    pools: dict = defaultdict(list)

    def add(kind: str, f: Fact, value: str, tag: str):
        if not value:
            return
        for key in ((kind, f.davr, tag), (kind, f.davr, ""), (kind, "", tag), (kind, "", "")):
            pools[key].append(value)

    for f in facts:
        if SKIP_FLAGS & set(f.flags or []):
            continue
        if f.tur == "shaxs":
            add("shaxs", f, f.nom, f.shaxs_faoliyati)
            add("shaxs", f, f.nom, f.hudud)
            add("shaxs", f, f.nom, f"{f.shaxs_faoliyati}|{f.hudud}")
            if f.shaxs_faoliyati in AUTHOR_JOBS:
                add("muallif", f, f.nom, f.hudud)
        elif f.tur == "atama":
            add("atama", f, f.nom, f.hudud)
        elif f.tur == "joy":
            add("joy", f, f.nom, f.joy_turi)
            add("joy", f, f.nom, f.hudud)
            add("joy", f, f.nom, f"{f.joy_turi}|{f.hudud}")
        elif f.tur == "asar":
            kind = "bino" if is_building(f) else "kitob"
            add("asar", f, work_title(f.nom), kind)
            add("asar", f, work_title(f.nom), f"{kind}|{f.hudud}")
            if f.asar_muallifi and len(f.asar_muallifi) <= 60:
                add("muallif", f, f.asar_muallifi, f.hudud)
        elif f.tur == "urush":
            for side in dict.fromkeys(clean_side(x) for x in [f.golib, *f.urush_tomonlari]):  # tartib barqaror
                add("golib", f, side, f.hudud)
    return pools


def generate(facts: list[Fact]) -> list[GenQuestion]:
    """Ko‘rinadigan faktlardan savollar ro‘yxati (har fakt — 0, 1 yoki 2 ta savol)."""
    facts = [f for f in facts if f.visible and not (SKIP_FLAGS & set(f.flags or []))]
    pools = _pools(facts)
    by_shape: dict[str, list] = defaultdict(list)
    for f in facts:
        if f.tur in ("sana", "urush") and f.sana_matn:
            shape, iv = date_shape(f.sana_matn), interval(f)
            if shape and iv:
                by_shape[shape].append((f, iv))

    out: list[GenQuestion] = []
    for f in facts:
        made: list[GenQuestion | None] = []
        if f.tur == "sana":
            made.append(_when_q(f, by_shape, "qachon"))
        elif f.tur == "shaxs":
            made.append(_who_q(f, pools))
        elif f.tur == "atama":
            made.append(_term_q(f, pools))
        elif f.tur == "joy":
            made.append(_place_q(f, pools))
        elif f.tur == "asar":
            made.append(_author_q(f, pools) if f.asar_muallifi else _work_q(f, pools))
        elif f.tur == "urush":
            made += [_winner_q(f, pools), _when_q(f, by_shape, "qachon")]
        out += [q for q in made if q is not None]
    return out


def question_leaks(q: GenQuestion) -> bool:
    """Xavfsizlik tekshiruvi: to‘g‘ri javob savol matnida ko‘rinib qolganmi."""
    answer = q.options["abcd".index(q.correct)]
    return _leaks(answer, q.text)


# ---------- Bazaga yozish ----------

@dataclass
class SyncReport:
    total: int = 0
    added: int = 0
    updated: int = 0
    unchanged: int = 0
    locked: int = 0
    deactivated: int = 0
    by_kind: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return self.__dict__.copy()


def _paragraf_no(p: str) -> int:
    m = re.search(r"\d+", p or "")
    return int(m.group()) if m else 999


async def _periods_topics(session, facts: list[Fact]) -> tuple[dict, dict]:
    """Davrlar (4 ta) va mavzular: darslik paragrafi (mavzu_nomi) -> Topic.
    Mavzu davri — undagi faktlarning ko'pchiligi davri; tartib — sinf va paragraf bo'yicha."""
    from sqlalchemy import select

    from app.models import Period, Topic

    periods = {}
    for i, name in enumerate(PERIOD_ORDER, start=1):
        p = await session.scalar(select(Period).where(Period.name == name))
        if p is None:
            p = Period(name=name, sort_order=i)
            session.add(p)
        periods[name] = p
    await session.flush()

    groups: dict[tuple[str, str], list[Fact]] = defaultdict(list)
    for f in facts:
        groups[(f.book_id, f.mavzu_nomi or "Boshqa mavzular")].append(f)
    # Bir davrda bir xil nomli mavzu bir nechta darslikda bo'lsa — sinf qo'shiladi
    names = defaultdict(set)
    meta = {}
    for (book, mavzu), fs in groups.items():
        davr = collections_mode([f.davr for f in fs])
        period = periods[DAVR_TO_PERIOD.get(davr, PERIOD_ORDER[0])]
        meta[(book, mavzu)] = (period, fs[0].sinf, min(_paragraf_no(f.paragraf) for f in fs))
        names[(period.name, mavzu)].add(book)

    existing = {(t.period_id, t.name): t for t in await session.scalars(select(Topic))}
    topics = {}
    for (book, mavzu), (period, sinf, par) in sorted(meta.items(), key=lambda kv: (kv[1][1], kv[1][2])):
        name = mavzu if len(names[(period.name, mavzu)]) == 1 else f"{mavzu} ({sinf}-sinf)"
        t = existing.get((period.id, name))
        order = sinf * 1000 + par
        if t is None:
            t = Topic(name=name, period_id=period.id, sort_order=order)
            session.add(t)
            existing[(period.id, name)] = t
        elif t.sort_order != order:
            t.sort_order = order
        topics[(book, mavzu)] = t
    await session.flush()
    return periods, topics


def collections_mode(values: list[str]) -> str:
    counts: dict[str, int] = defaultdict(int)
    for v in values:
        counts[v] += 1
    return max(counts, key=counts.get) if counts else ""


async def sync_questions(session) -> SyncReport:
    """Faktlardan savollarni tuzib, bazaga yozadi (gen_key bo'yicha yangilaydi).
    Admin tahrirlagan (locked) savollarga tegilmaydi; endi tuzilmaydigan savollar o'chiriladi."""
    from sqlalchemy import select

    from app.models import Question

    facts = list(await session.scalars(select(Fact)))
    gens = generate(facts)
    _, topics = await _periods_topics(session, [f for f in facts if f.visible])
    existing = {q.gen_key: q for q in await session.scalars(select(Question).where(Question.gen_key.is_not(None)))}
    rep = SyncReport(total=len(gens))
    seen = set()
    for g in gens:
        seen.add(g.key)
        rep.by_kind[g.kind] = rep.by_kind.get(g.kind, 0) + 1
        topic = topics.get((g.fact.book_id, g.fact.mavzu_nomi or "Boshqa mavzular"))
        values = {
            "text": g.text, "option_a": g.options[0], "option_b": g.options[1], "option_c": g.options[2],
            "option_d": g.options[3], "correct_option": g.correct, "explanation": g.explanation,
            "difficulty": g.difficulty, "asks_time": g.asks_time, "fact_id": g.fact.id,
            "topic_id": topic.id if topic else None, "period_id": topic.period_id if topic else None,
            "is_active": True,
        }
        q = existing.get(g.key)
        if q is None:
            session.add(Question(gen_key=g.key, **values))
            rep.added += 1
        elif q.locked:
            rep.locked += 1
        elif any(getattr(q, k) != v for k, v in values.items()):
            for k, v in values.items():
                setattr(q, k, v)
            rep.updated += 1
        else:
            rep.unchanged += 1
    for key, q in existing.items():
        if key not in seen and not q.locked and q.is_active:
            q.is_active = False
            rep.deactivated += 1
    await session.flush()
    return rep
