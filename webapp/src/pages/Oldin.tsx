import { useCallback, useEffect, useRef, useState } from "react";
import { Book, Calendar, Check, Clock, Close, Cross, Refresh } from "../components/Icons";
import { Bar, Card, IconTile, Pill, cx } from "../components/kit";
import { Loading, toast } from "../components/ui";
import { api } from "../lib/api";
import { navigate } from "../lib/router";
import { useStore } from "../lib/store";
import { confirmDialog, haptic } from "../lib/telegram";

type Side = { id: string; title: string; meta: string; year?: string; source?: string };
type Pair = { index: number; total: number; a: Side; b: Side };
type Info = { xp_today: number; xp_cap: number; rounds_today: number; can_resume: boolean; pairs: number; seconds: number };
type Answer = { correct: boolean; earlier: "a" | "b"; a: Side; b: Side; points: number; score: number; combo: number; multiplier: number; left_ms: number; last: boolean };
type Result = {
  round: number; correct: number; wrong: number; answered: number; total: number; score: number; best_combo: number;
  accuracy: number; xp: number; xp_note: string; xp_today: number; xp_cap: number;
  mistakes: { a: Side; b: Side; picked: "a" | "b"; earlier: "a" | "b" }[];
};

const wrap = "mx-auto max-w-[560px] px-4";
const roundNote = (n: number) => (n <= 2 ? "XP to‘liq" : n === 3 ? "XP yarim" : "XP berilmaydi");

function EventCard({ side, which, ans, picked, disabled, onPick }: {
  side: Side; which: "a" | "b"; ans: Answer | null; picked: "a" | "b" | null; disabled: boolean; onPick: () => void;
}) {
  const shown = ans ? ans[which] : side;
  const isEarlier = ans?.earlier === which;
  const wrongPick = ans && picked === which && !ans.correct;
  return (
    <button type="button" disabled={disabled} onClick={onPick}
      className={cx(
        "relative w-full rounded-card border-2 bg-surface p-5 text-left shadow-soft transition",
        !ans && "border-line hover:border-peri active:scale-[.99]",
        ans && isEarlier && "border-success bg-success-soft",
        ans && !isEarlier && (wrongPick ? "border-danger bg-danger-soft" : "border-line opacity-80"),
      )}>
      {ans && (
        <span className={cx("absolute right-4 top-4 rounded-full px-2.5 py-1 text-[12px] font-bold",
          isEarlier ? "bg-success text-on-success" : "bg-surface-2 text-muted")}>
          {isEarlier ? "Oldin" : "Keyin"}
        </span>
      )}
      <div className="pr-16 font-reading text-[19px] font-semibold leading-snug text-ink">{shown.title}</div>
      {ans ? (
        <>
          <div className={cx("mt-2 text-[22px] font-extrabold tracking-tight", isEarlier ? "text-success" : "text-ink")}>{shown.year}</div>
          <div className="mt-1 flex items-start gap-1.5 text-[12.5px] text-muted"><Book size={14} className="mt-0.5 shrink-0" />{shown.source}</div>
        </>
      ) : (
        <div className="mt-2 text-[13px] text-muted">{shown.meta}</div>
      )}
    </button>
  );
}

export function OldinPage() {
  const { reload } = useStore();
  const [info, setInfo] = useState<Info | null>(null);
  const [phase, setPhase] = useState<"intro" | "count" | "play" | "result">("intro");
  const [count, setCount] = useState(3);
  const [sid, setSid] = useState(0);
  const [pair, setPair] = useState<Pair | null>(null);
  const [ans, setAns] = useState<Answer | null>(null);
  const [picked, setPicked] = useState<"a" | "b" | null>(null);
  const [score, setScore] = useState(0);
  const [mult, setMult] = useState(1);
  const [left, setLeft] = useState(60_000);
  const [result, setResult] = useState<Result | null>(null);
  const [busy, setBusy] = useState(false);
  const deadline = useRef<number | null>(null); // soat yurayotganda: performance.now() bo'yicha tugash vaqti
  const finishing = useRef(false);

  const loadInfo = useCallback(() => api<Info>("/v1/games/oldin").then(setInfo).catch((e) => toast(e.message, "error")), []);
  useEffect(() => { void loadInfo(); }, [loadInfo]);
  useEffect(() => {
    document.body.classList.add("hide-nav");
    return () => document.body.classList.remove("hide-nav");
  }, []);

  const finish = useCallback(async (id: number) => {
    if (finishing.current) return;
    finishing.current = true;
    deadline.current = null;
    try {
      setResult(await api<Result>(`/v1/games/${id}/finish`, { method: "POST" }));
      setPhase("result");
      haptic.success();
      void reload();
    } catch (e) {
      finishing.current = false;
      toast((e as Error).message, "error");
    }
  }, [reload]);

  // Soat: faqat savol ochiq turganda yuradi (server ham shunday hisoblaydi)
  useEffect(() => {
    if (phase !== "play") return;
    const t = setInterval(() => {
      if (deadline.current === null) return;
      const l = Math.max(0, deadline.current - performance.now());
      setLeft(l);
      if (l <= 0) void finish(sid);
    }, 100);
    return () => clearInterval(t);
  }, [phase, sid, finish]);

  async function begin() {
    setPhase("count");
    for (const n of [3, 2, 1]) {
      setCount(n);
      haptic.tap();
      await new Promise((r) => setTimeout(r, 650));
    }
    try {
      const st = await api<{ session_id: number; pair: Pair | null; left_ms: number; score: number; combo: number }>("/v1/games/oldin/start", { method: "POST" });
      finishing.current = false;
      setSid(st.session_id);
      setScore(st.score);
      setMult(st.combo >= 6 ? 3 : st.combo >= 3 ? 2 : 1);
      setResult(null);
      if (!st.pair) return finish(st.session_id);
      setPair(st.pair);
      setAns(null);
      setPicked(null);
      setLeft(st.left_ms);
      deadline.current = performance.now() + st.left_ms;
      setPhase("play");
    } catch (e) {
      toast((e as Error).message, "error");
      setPhase("intro");
    }
  }

  async function pick(which: "a" | "b") {
    if (busy || ans) return;
    setBusy(true);
    setPicked(which);
    try {
      const r = await api<Answer>(`/v1/games/${sid}/answer`, { body: { pick: which } });
      deadline.current = null; // izoh o'qilayotganda soat to'xtaydi
      setLeft(r.left_ms);
      setAns(r);
      setScore(r.score);
      setMult(r.multiplier);
      if (r.correct) haptic.success(); else haptic.error();
    } catch (e) {
      toast((e as Error).message, "error");
      void finish(sid);
    } finally {
      setBusy(false);
    }
  }

  async function next() {
    if (!ans) return;
    if (ans.last || left <= 0) return finish(sid);
    setBusy(true);
    try {
      const r = await api<{ pair: Pair | null; left_ms: number; finished: boolean }>(`/v1/games/${sid}/next`, { method: "POST" });
      if (r.finished || !r.pair) return finish(sid);
      setPair(r.pair);
      setAns(null);
      setPicked(null);
      setLeft(r.left_ms);
      deadline.current = performance.now() + r.left_ms;
    } catch (e) {
      toast((e as Error).message, "error");
    } finally {
      setBusy(false);
    }
  }

  async function quit() {
    if (phase === "play" && !(await confirmDialog("O‘yinni to‘xtatasizmi? Keyin davom ettirishingiz mumkin."))) return;
    void reload();
    navigate("/mashq", true);
  }

  if (!info) return <Loading />;

  // ---------- Kirish ----------
  if (phase === "intro") {
    const round = info.rounds_today + (info.can_resume ? 0 : 1);
    return (
      <div className={cx(wrap, "space-y-4 pb-[calc(var(--safe-bottom)+110px)] pt-[calc(var(--safe-top)+12px)]")}>
        <button type="button" onClick={quit} aria-label="Yopish" className="grid h-9 w-9 place-items-center rounded-full text-muted hover:bg-surface-2"><Close size={20} /></button>
        <div className="flex items-center gap-4">
          <IconTile tone="sana" size={56}><Calendar size={26} /></IconTile>
          <div>
            <div className="text-[12px] font-bold uppercase tracking-[.1em] text-muted">Sana o‘yini</div>
            <h1 className="text-[27px] font-extrabold tracking-tight text-ink">Qaysi biri oldin?</h1>
          </div>
        </div>
        <Card className="space-y-3 p-5">
          {[
            [`${info.seconds} soniya, ${info.pairs} juftlik`, "Ikki voqeadan oldin bo‘lganini tanlang."],
            ["Oraliq asta torayadi", "500 yildan boshlanib, oxirida 10 yildan kam farq."],
            ["Seriya ochkoni oshiradi", "Ketma-ket 3 ta to‘g‘ri — ×2, 6 ta — ×3. Xato seriyani nolga tushiradi."],
            ["Izoh paytida soat to‘xtaydi", "Javobdan keyin ikkala yil va darslik betini bemalol o‘qing."],
            ["Xatolar takrorlashga tushadi", "Adashgan voqealar kunlik takrorlashda qaytadi."],
          ].map(([t, d], i) => (
            <div key={t} className="flex gap-3">
              <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-peri-soft text-[12px] font-bold text-peri">{i + 1}</span>
              <div><div className="text-[15px] font-semibold text-ink">{t}</div><div className="text-[13.5px] text-muted">{d}</div></div>
            </div>
          ))}
        </Card>
        <Card className="p-4">
          <div className="flex items-center justify-between text-[14px]">
            <span className="font-semibold text-ink">Bugungi XP</span>
            <span className="font-bold text-ink">{info.xp_today} / {info.xp_cap}</span>
          </div>
          <Bar value={info.xp_today / info.xp_cap} className="mt-2" tone="bg-sana" />
          <div className="mt-2 text-[12.5px] text-muted">{round}-raund · {roundNote(round)}</div>
        </Card>
        <div className="fixed inset-x-0 bottom-0 border-t border-line bg-surface/95 backdrop-blur">
          <div className={cx(wrap, "py-3 pb-[calc(var(--safe-bottom)+12px)]")}>
            <button type="button" onClick={begin} className="w-full rounded-full bg-cta py-3.5 text-[16px] font-bold text-on-cta active:scale-[.99]">
              {info.can_resume ? "Davom ettirish" : "Boshlash"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ---------- 3-2-1 ----------
  if (phase === "count") {
    return (
      <div className="grid min-h-screen place-items-center">
        <div key={count} className="rise text-[96px] font-extrabold leading-none tracking-tight text-ink">{count}</div>
      </div>
    );
  }

  // ---------- Natija ----------
  if (phase === "result" && result) {
    return (
      <div className={cx(wrap, "space-y-4 pb-[calc(var(--safe-bottom)+120px)] pt-[calc(var(--safe-top)+24px)]")}>
        <div className="rise text-center">
          <div className="text-[12px] font-bold uppercase tracking-[.12em] text-muted">Qaysi biri oldin? · {result.round}-raund</div>
          <div className="mt-2 text-[56px] font-extrabold leading-none tracking-tight text-ink">{result.score}</div>
          <div className="text-[14px] text-muted">ochko</div>
        </div>
        <div className="grid grid-cols-4 gap-2">
          {[["To‘g‘ri", result.correct, "text-success"], ["Xato", result.wrong, "text-danger"],
            ["Aniqlik", `${result.accuracy}%`, "text-ink"], ["Seriya", result.best_combo, "text-ink"]].map(([l, v, c]) => (
            <Card key={String(l)} className="p-3 text-center">
              <div className={cx("text-[20px] font-extrabold", String(c))}>{v}</div>
              <div className="text-[11.5px] font-medium text-muted">{l}</div>
            </Card>
          ))}
        </div>
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <span className="text-[15px] font-bold text-ink">+{result.xp} XP</span>
            <span className="text-[13px] text-muted">bugun {result.xp_today} / {result.xp_cap}</span>
          </div>
          <div className="mt-1 text-[12.5px] text-muted">{result.xp_note}</div>
          <Bar value={result.xp_today / result.xp_cap} className="mt-2" tone="bg-sana" />
        </Card>

        {result.mistakes.length > 0 && (
          <>
            <div className="flex items-end justify-between px-1 pt-2">
              <h2 className="text-[18px] font-bold text-ink">Xato qilingan juftliklar</h2>
              <Pill className="bg-danger-soft text-danger">takrorlashga qo‘shildi</Pill>
            </div>
            {result.mistakes.map((m, i) => (
              <Card key={i} className="divide-y divide-line overflow-hidden">
                {(["a", "b"] as const).map((w) => (
                  <div key={w} className="flex items-start gap-3 p-3.5">
                    <span className={cx("mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full",
                      m.earlier === w ? "bg-success text-on-success" : m.picked === w ? "bg-danger text-white" : "bg-surface-2 text-muted")}>
                      {m.earlier === w ? <Check size={14} /> : m.picked === w ? <Cross size={14} /> : null}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="text-[14.5px] font-semibold leading-snug text-ink">{m[w].title}</div>
                      <div className="text-[13px] font-bold text-ink-2">{m[w].year}</div>
                      <div className="text-[12px] text-muted">{m[w].source}</div>
                    </div>
                  </div>
                ))}
              </Card>
            ))}
          </>
        )}

        <div className="fixed inset-x-0 bottom-0 border-t border-line bg-surface/95 backdrop-blur">
          <div className={cx(wrap, "grid grid-cols-2 gap-3 py-3 pb-[calc(var(--safe-bottom)+12px)]")}>
            <button type="button" onClick={() => navigate("/mashq", true)} className="rounded-full border border-line-strong bg-surface py-3.5 text-[15px] font-bold text-ink">Mashq</button>
            <button type="button" onClick={() => { void loadInfo(); setPhase("intro"); }}
              className="inline-flex items-center justify-center gap-2 rounded-full bg-cta py-3.5 text-[15px] font-bold text-on-cta"><Refresh size={17} /> Qayta o‘ynash</button>
          </div>
        </div>
      </div>
    );
  }

  // ---------- O'yin ----------
  if (!pair) return <Loading />;
  const secs = Math.ceil(left / 1000);
  return (
    <div className="min-h-screen pb-[calc(var(--safe-bottom)+110px)]">
      <div className={cx(wrap, "sticky top-0 z-10 space-y-2 bg-canvas/90 pb-3 pt-[calc(var(--safe-top)+12px)] backdrop-blur")}>
        <div className="flex items-center gap-3">
          <button type="button" onClick={quit} aria-label="Yopish" className="grid h-9 w-9 place-items-center rounded-full text-muted hover:bg-surface-2"><Close size={20} /></button>
          <span className={cx("inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[15px] font-extrabold tabular-nums",
            secs <= 10 ? "bg-danger-soft text-danger" : "bg-surface text-ink shadow-soft")}>
            <Clock size={16} /> {secs}s
          </span>
          {!deadline.current && ans && <span className="text-[12px] font-semibold text-muted">soat to‘xtagan</span>}
          <span className="flex-1" />
          {mult > 1 && <span className="rounded-full bg-peach px-2.5 py-1 text-[13px] font-extrabold text-white">×{mult}</span>}
          <span className="text-[18px] font-extrabold tabular-nums text-ink">{score}</span>
        </div>
        <Bar value={left / (info.seconds * 1000)} tone={secs <= 10 ? "bg-danger" : "bg-sana"} className="h-1.5" />
      </div>

      <div className={cx(wrap, "space-y-3")}>
        <div className="flex items-center justify-between px-1">
          <span className="text-[13px] font-bold uppercase tracking-[.1em] text-muted">Qaysi biri oldin bo‘lgan?</span>
          <span className="text-[13px] font-bold tabular-nums text-muted">{pair.index}/{pair.total}</span>
        </div>
        <div key={pair.index} className="rise space-y-3">
          <EventCard side={pair.a} which="a" ans={ans} picked={picked} disabled={busy || !!ans} onPick={() => pick("a")} />
          <div className="text-center text-[12px] font-bold uppercase tracking-[.2em] text-faint">yoki</div>
          <EventCard side={pair.b} which="b" ans={ans} picked={picked} disabled={busy || !!ans} onPick={() => pick("b")} />
        </div>
        {ans && (
          <div className={cx("rise text-center text-[15px] font-bold", ans.correct ? "text-success" : "text-danger")}>
            {ans.correct ? `To‘g‘ri! +${ans.points}${ans.multiplier > 1 ? ` (×${ans.multiplier})` : ""}` : "Xato — seriya nolga tushdi"}
          </div>
        )}
      </div>

      {ans && (
        <div className="fixed inset-x-0 bottom-0 z-20 border-t border-line bg-surface/95 backdrop-blur">
          <div className={cx(wrap, "py-3 pb-[calc(var(--safe-bottom)+12px)]")}>
            <button type="button" disabled={busy} onClick={next}
              className="w-full rounded-full bg-cta py-3.5 text-[16px] font-bold text-on-cta active:scale-[.99] disabled:opacity-60">
              {ans.last || left <= 0 ? "Natijani ko‘rish" : "Keyingi"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
