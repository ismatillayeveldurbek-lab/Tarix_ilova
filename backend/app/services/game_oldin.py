""""Qaysi biri oldin?" — 60 soniyalik blits (docs/mezon-tahlili.md → O'yinlar).

* 24 juftlik. Ikki voqeadan oldin bo'lganini tanlaysiz.
* Juftlik oralig'i asta torayadi: 500+, 100+, 30+, 10+ va 10 yildan kam.
* Ochko: to'g'ri javob +10; ketma-ket 3 ta to'g'ri — x2, 6 ta — x3; xato — kombo nolga tushadi.
* Javobdan keyin ikkala yil va darslik beti ko'rsatiladi; izoh o'qilayotganda soat TO'XTAYDI.
* Xato qilingan juftlikdagi ikkala voqea kunlik takrorlashga tushadi ("Takrorlash kerak").
* XP: har to'g'ri javob 3 XP; bugungi 1–2-raund to'liq, 3-raund yarim, 4-raunddan XP yo'q;
  bu o'yindan kuniga ko'pi bilan 100 XP. XP haftalik reytingga qo'shiladi.
"""
import bisect
import random
import re
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import local_today, utcnow
from app.models import Fact, GameSession, User, UserFactState, XpBonus
from app.services.daily import local_midnight_utc
from app.services.facts import VISIBLE, get_daily_stat
from app.services.facts_validation import NO_YEAR_GAME_FLAGS, roman_to_int
from app.services.srs import schedule
from app.services.streak import touch_streak

GAME = "oldin"
PAIRS = 24
BUDGET_MS = 60_000
GRACE_MS = 1_500                        # internet kechikishi uchun
TIERS = [(500, None), (100, 499), (30, 99), (10, 29), (1, 9)]   # har 5 juftlikda torayadi
POINTS = 10
XP_PER_CORRECT = 3
DAILY_XP_CAP = 100


class GameError(Exception):
    pass


# ---------- Juftliklar ----------

_ROMAN_RE = re.compile(r"\b[IVXL]+\b")


def _century_span(c: int, bc: bool) -> tuple[int, int]:
    lo, hi = (c - 1) * 100 + 1, c * 100
    return (-hi, -lo) if bc else (lo, hi)


def interval(f: Fact) -> tuple[int, int] | None:
    """Voqea vaqti ORALIQ sifatida: "XV asr" -> 1401–1500, "XV asrning 60-yillari" -> 1460–1469,
    "1572, 1577-yillar" -> 1572–1577, "mil. avv. 6–4-mingyilliklar" -> -6000…-3001.
    Sana noaniq bo'lsa ("Shohmurod davri") — None (o'yinga kirmaydi)."""
    if f.yil_boshi is None:
        return None
    raw = f.sana_matn or ""
    s = raw.lower()
    bc = "mil. avv" in s or f.yil_boshi < 0
    base = [f.yil_boshi] + ([f.yil_oxiri] if f.yil_oxiri is not None else [])
    if "mingyillik" in s:
        nums = [int(n) for n in re.findall(r"\d+", s)]
        if nums:
            lo, hi = min(nums), max(nums)
            return (-hi * 1000, -(lo - 1) * 1000 - 1) if bc else ((lo - 1) * 1000 + 1, hi * 1000)
    romans = [roman_to_int(r) for r in _ROMAN_RE.findall(raw)]
    decade = re.search(r"(\d{1,2})-yillar", s)
    if romans and decade and "asr" in s:  # XV asrning 60-yillari
        start = (romans[0] - 1) * 100 + int(decade.group(1))
        return (-(start + 9), -start) if bc else (start, start + 9)
    years = [int(n) for n in re.findall(r"(\d{3,4})(?=\s*-?yil|\s*[,;–-])", s)]
    if years:
        years = [-y for y in years] if bc else years
        lo, hi = min(years + base), max(years + base)
        if re.search(r"\d{3,4}-yillar\b", s) and len(set(years)) == 1:  # "1990-yillar" — o'n yillik
            hi = max(hi, lo + 9) if not bc else hi
        return lo, hi
    if romans and "asr" in s:  # XV asr / XIV–XV asrlar
        spans = [_century_span(c, bc) for c in romans]
        return min(x[0] for x in spans), max(x[1] for x in spans)
    if re.search(r"\d", s) or not s:
        return min(base), max(base)
    return None  # so'z bilan berilgan noaniq sana


def eligible(f: Fact) -> bool:
    """O'yinga yaroqli voqea: vaqti aniq oraliq, nomida raqam yo'q (javob ko'rinmasin)."""
    return (f.tur in ("sana", "urush") and f.visible
            and not (set(f.flags or []) & (NO_YEAR_GAME_FLAGS | {"kontekstsiz"}))
            and not any(ch.isdigit() for ch in f.nom) and interval(f) is not None)


def earlier_of(a: Fact, b: Fact) -> str | None:
    """"a" yoki "b"; oraliqlar kesishsa — None (bunday juftlik tuzilmaydi)."""
    ia, ib = interval(a), interval(b)
    if ia[1] < ib[0]:
        return "a"
    if ib[1] < ia[0]:
        return "b"
    return None


def gap(a: Fact, b: Fact) -> int:
    ia, ib = interval(a), interval(b)
    return max(ib[0] - ia[1], ia[0] - ib[1])


def make_pairs(facts: list[Fact], n: int = PAIRS, rng: random.Random | None = None) -> list[tuple[str, str]]:
    """Juftliklar: oraliq har bosqichda torayadi. Voqealar vaqti kesishmaydi (javob bir ma'noli),
    voqea takrorlanmaydi."""
    rng = rng or random.Random()
    pool = [f for f in facts if eligible(f)]
    spans = {f.id: interval(f) for f in pool}
    by_start = sorted(pool, key=lambda f: spans[f.id][0])
    starts = [spans[f.id][0] for f in by_start]
    used: set[str] = set()
    pairs: list[tuple[str, str]] = []
    per_tier = max(1, n // len(TIERS))
    for i in range(n):
        lo, hi = TIERS[min(i // per_tier, len(TIERS) - 1)]
        hi = hi if hi is not None else 10**7
        for _ in range(80):
            a = rng.choice(pool)
            if a.id in used:
                continue
            a_end = spans[a.id][1]
            # a dan KEYIN boshlangan b: b.start - a.end oralig'i [lo, hi]
            l_i, r_i = bisect.bisect_left(starts, a_end + lo), bisect.bisect_right(starts, a_end + hi)
            cands = [f for f in by_start[l_i:r_i] if f.id not in used]
            if not cands:
                continue
            b = rng.choice(cands)
            used.update((a.id, b.id))
            pairs.append((a.id, b.id) if rng.random() < .5 else (b.id, a.id))
            break
    return pairs


# ---------- Soat ----------

def raw_left_ms(s: GameSession, now: datetime | None = None) -> int:
    """Qolgan vaqt (manfiy bo'lishi mumkin — vaqt qancha oshib ketganini ko'rsatadi)."""
    used = s.used_ms
    if s.running and s.resumed_at:
        used += int(((now or utcnow()) - s.resumed_at) / timedelta(milliseconds=1))
    return s.budget_ms - used


def left_ms(s: GameSession, now: datetime | None = None) -> int:
    return max(0, raw_left_ms(s, now))


def pause(s: GameSession, now: datetime) -> None:
    if s.running and s.resumed_at:
        s.used_ms += int((now - s.resumed_at) / timedelta(milliseconds=1))
    s.running = False


def resume(s: GameSession, now: datetime) -> None:
    s.running, s.resumed_at = True, now


# ---------- Ko'rsatish ----------

def year_text(f: Fact) -> str:
    if f.sana_matn:
        return f.sana_matn
    y = f.yil_boshi
    return f"mil. avv. {-y}-yil" if y < 0 else f"{y}-yil"


def card_front(f: Fact) -> dict:
    """Voqea kartasi javobdan OLDIN: faqat nom. Yil ham, darslik/sinf ham yuborilmaydi —
    sinf davrni bildiradi (6-sinf — qadimgi, 11-sinf — eng yangi) va javobni aytib qo'yadi."""
    return {"id": f.id, "title": f.nom}


def card_back(f: Fact) -> dict:
    """Javobdan keyin: yil va darslik manbasi."""
    return {**card_front(f), "year": year_text(f), "source": f.source}


# ---------- Sessiya ----------

async def rounds_today(session: AsyncSession, user: User) -> int:
    return await session.scalar(select(func.count()).select_from(GameSession).where(
        GameSession.user_id == user.id, GameSession.game == GAME, GameSession.started_at >= local_midnight_utc())) or 0


async def open_session(session: AsyncSession, user: User) -> GameSession | None:
    s = await session.scalar(select(GameSession).where(
        GameSession.user_id == user.id, GameSession.game == GAME, GameSession.finished_at.is_(None))
        .order_by(GameSession.id.desc()).limit(1))
    return s


async def start(session: AsyncSession, user: User, rng: random.Random | None = None) -> GameSession:
    current = await open_session(session, user)
    if current is not None:
        if left_ms(current) > 0 and current.state["idx"] < len(current.state["pairs"]):
            return current  # to'xtagan joyidan davom etadi
        await finish(session, user, current)
    facts = list(await session.scalars(
        select(Fact).where(VISIBLE, Fact.yil_boshi.is_not(None), Fact.tur.in_(("sana", "urush")))))
    pairs = make_pairs(facts, rng=rng)
    if len(pairs) < 5:
        raise GameError("O‘yin uchun voqealar yetarli emas")
    now = utcnow()
    s = GameSession(
        user_id=user.id, game=GAME, round_no=await rounds_today(session, user) + 1, started_at=now,
        budget_ms=BUDGET_MS, used_ms=0, running=True, resumed_at=now, xp=0,
        state={"pairs": [{"a": a, "b": b, "pick": None, "ok": None, "points": 0} for a, b in pairs],
               "idx": 0, "score": 0, "combo": 0, "best_combo": 0},
    )
    session.add(s)
    await session.flush()
    return s


async def current_pair(session: AsyncSession, s: GameSession) -> dict | None:
    st = s.state
    if st["idx"] >= len(st["pairs"]):
        return None
    p = st["pairs"][st["idx"]]
    a, b = await session.get(Fact, p["a"]), await session.get(Fact, p["b"])
    return {"index": st["idx"] + 1, "total": len(st["pairs"]), "a": card_front(a), "b": card_front(b)}


def multiplier(combo: int) -> int:
    return 3 if combo >= 6 else 2 if combo >= 3 else 1


async def answer(session: AsyncSession, s: GameSession, pick: str, now: datetime | None = None) -> dict:
    now = now or utcnow()
    if s.finished_at is not None:
        raise GameError("O‘yin yakunlangan")
    if not s.running:
        raise GameError("Avval keyingi juftlikka o‘ting")
    if raw_left_ms(s, now) < -GRACE_MS:  # kechikkan javobga 1,5 soniya imkon
        raise GameError("Vaqt tugadi")
    st = {**s.state, "pairs": [dict(p) for p in s.state["pairs"]]}
    p = st["pairs"][st["idx"]]
    a, b = await session.get(Fact, p["a"]), await session.get(Fact, p["b"])
    earlier = earlier_of(a, b)
    ok = pick == earlier
    if ok:
        st["combo"] += 1
        p["points"] = POINTS * multiplier(st["combo"])
        st["score"] += p["points"]
        st["best_combo"] = max(st["best_combo"], st["combo"])
    else:
        st["combo"] = 0
    p["pick"], p["ok"] = pick, ok
    pause(s, now)  # izoh o'qilayotganda soat to'xtaydi
    st["idx"] += 1
    s.state = st
    await session.flush()
    return {
        "correct": ok, "earlier": earlier, "a": card_back(a), "b": card_back(b),
        "points": p["points"], "score": st["score"], "combo": st["combo"], "multiplier": multiplier(st["combo"]),
        "left_ms": left_ms(s, now), "last": st["idx"] >= len(st["pairs"]),
    }


async def next_pair(session: AsyncSession, s: GameSession, now: datetime | None = None) -> dict | None:
    now = now or utcnow()
    if s.finished_at is not None or left_ms(s, now) <= 0:
        return None
    pair = await current_pair(session, s)
    if pair is not None and not s.running:
        resume(s, now)
        await session.flush()
    return pair


def xp_for_round(correct: int, round_no: int, earned_today: int) -> tuple[int, str]:
    raw = correct * XP_PER_CORRECT
    if round_no >= 4:
        return 0, "4-raunddan boshlab XP berilmaydi — ertaga yana to‘liq"
    if round_no == 3:
        raw //= 2
    left = max(0, DAILY_XP_CAP - earned_today)
    xp = min(raw, left)
    note = f"{correct} to‘g‘ri × {XP_PER_CORRECT} XP" + (" · 3-raund: yarim" if round_no == 3 else "")
    if xp < raw:
        note += f" · kunlik {DAILY_XP_CAP} XP limiti"
    return xp, note


async def finish(session: AsyncSession, user: User, s: GameSession, now: datetime | None = None) -> dict:
    now = now or utcnow()
    st = s.state
    answered = [p for p in st["pairs"] if p["pick"] is not None]
    correct = sum(1 for p in answered if p["ok"])
    mistakes = [p for p in answered if not p["ok"]]
    if s.finished_at is None:
        pause(s, now)
        stat = await get_daily_stat(session, user.id, create=True)
        earned_today = int((stat.game_xp or {}).get(GAME, 0))
        s.xp, _ = xp_for_round(correct, s.round_no, earned_today)
        s.finished_at = now
        stat.game_xp = {**(stat.game_xp or {}), GAME: earned_today + s.xp}
        stat.xp += s.xp
        stat.games_played += 1
        if s.xp:
            session.add(XpBonus(user_id=user.id, amount=s.xp, reason="oyin_oldin"))
        if answered:
            touch_streak(user)
        # Xato qilingan voqealar kunlik takrorlashga ("Takrorlash kerak")
        for p in mistakes:
            for fid in (p["a"], p["b"]):
                state = await session.scalar(select(UserFactState).where(
                    UserFactState.user_id == user.id, UserFactState.fact_id == fid))
                if state is None:
                    state = UserFactState(user_id=user.id, fact_id=fid, holat="yangi", step=0,
                                          correct_count=0, wrong_count=0)
                    session.add(state)
                schedule(state, False, now)
        await session.flush()

    stat = await get_daily_stat(session, user.id)
    _, note = xp_for_round(correct, s.round_no, int((stat.game_xp or {}).get(GAME, 0)) - s.xp if stat else 0)
    mistake_cards = []
    for p in mistakes:
        a, b = await session.get(Fact, p["a"]), await session.get(Fact, p["b"])
        mistake_cards.append({"a": card_back(a), "b": card_back(b), "picked": p["pick"],
                              "earlier": earlier_of(a, b)})
    return {
        "session_id": s.id, "round": s.round_no, "correct": correct, "wrong": len(mistakes),
        "answered": len(answered), "total": len(st["pairs"]), "score": st["score"], "best_combo": st["best_combo"],
        "accuracy": round(100 * correct / len(answered)) if answered else 0,
        "xp": s.xp, "xp_note": note, "xp_today": int((stat.game_xp or {}).get(GAME, 0)) if stat else s.xp,
        "xp_cap": DAILY_XP_CAP, "mistakes": mistake_cards, "today": local_today().isoformat(),
    }
