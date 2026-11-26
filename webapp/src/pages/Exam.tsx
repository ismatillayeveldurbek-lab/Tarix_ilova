import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ChevronLeft, ChevronRight, Clipboard, Clock, Close } from "../components/Icons";
import { CountUp } from "../components/CountUp";
import { QuestionView } from "../components/QuestionView";
import { Bar, Card, HeroCard, Pill, Screen, SectionTitle, cx } from "../components/kit";
import { Confetti, ProgressRing } from "../components/motion";
import { Loading, Sheet, toast } from "../components/ui";
import { api } from "../lib/api";
import { navigate } from "../lib/router";
import { useStore } from "../lib/store";
import { confirmDialog, haptic, tg } from "../lib/telegram";
import type { Question } from "../lib/types";

type Info = {
  config: { name: string; count: number; minutes: number; max_score: number; grades: { min_percent: number; grade: string }[] } | null;
  open_exam_id: number | null;
  history: { id: number; date: string; score: number; grade: string }[];
};
type Running = { id: number; name: string; deadline: string; now: string; questions: Question[] };
type ResultItem = Question & { correct_option: string; is_correct: boolean; explanation: string; points: number };
const wrap = "mx-auto max-w-[560px] px-4";
type Result = { score: number; max_score: number; percent: number; grade: string; correct: number; total: number; items: ResultItem[] };

export function ExamPage() {
  const [info, setInfo] = useState<Info | null>(null);
  const [running, setRunning] = useState<Running | null>(null);
  const [result, setResult] = useState<Result | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => api<Info>("/exam").then(setInfo).catch((e) => toast(e.message, "error")), []);
  useEffect(() => { void load(); }, [load]);

  async function start() {
    setBusy(true);
    try {
      setRunning(await api<Running>("/exam/start", { method: "POST" }));
      haptic.tap();
    } catch (e) {
      toast((e as Error).message, "error");
    } finally {
      setBusy(false);
    }
  }

  // Imtihon va natija ekranida pastki menyu yashiriladi (tugmalarni to‘smasin)
  useEffect(() => {
    document.body.classList.toggle("hide-nav", !!(running || result));
    return () => document.body.classList.remove("hide-nav");
  }, [running, result]);

  if (result) return <ExamResult result={result} onDone={() => { setResult(null); void load(); }} />;
  if (running) return <ExamRunner exam={running} onFinish={(r) => { setRunning(null); setResult(r); }} />;
  if (!info) return <Loading />;
  return <ExamIntro info={info} busy={busy} onStart={start} />;
}

function ExamIntro({ info, busy, onStart }: { info: Info; busy: boolean; onStart: () => void }) {
  const c = info.config;
  if (!c) {
    return (
      <Screen>
        <Card className="flex flex-col items-center gap-2 p-8 text-center">
          <span className="grid h-14 w-14 animate-pop place-items-center rounded-2xl bg-shaxs-soft text-shaxs"><Clipboard size={26} /></span>
          <div className="text-[15px] text-muted">Imtihon formati hali sozlanmagan.</div>
        </Card>
      </Screen>
    );
  }
  return (
    <Screen>
      <HeroCard>
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-[12px] font-semibold uppercase tracking-[.12em] text-white/65">Sinov imtihoni</div>
            <h1 className="mt-1 text-[24px] font-extrabold leading-tight tracking-tight">{c.name}</h1>
          </div>
          <span className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-white/12"><Clipboard size={24} /></span>
        </div>
        <div className="mt-5 grid grid-cols-3 gap-2">
          {[["Savollar", c.count], ["Daqiqa", c.minutes], ["Maks. ball", c.max_score]].map(([l, v]) => (
            <div key={String(l)} className="rounded-2xl bg-white/[.08] px-3 py-2.5">
              <div className="text-[11.5px] font-medium text-white/60">{l}</div>
              <div className="text-[20px] font-bold tabular-nums">{v}</div>
            </div>
          ))}
        </div>
      </HeroCard>

      <Card className="space-y-3 p-4">
        <div className="text-[16px] font-bold text-ink">Qoidalar</div>
        {[
          "Taymer boshlangach to‘xtamaydi. Vaqt tugasa, imtihon avtomatik yakunlanadi.",
          "Javoblar darhol saqlanadi — ilovani yopsangiz, qaytib davom ettira olasiz.",
          "Savollar orasida bemalol o‘tishingiz mumkin. Izohlar imtihon oxirida ko‘rsatiladi.",
        ].map((t, i) => (
          <div key={i} className="flex gap-3">
            <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-peri-soft text-[12px] font-bold text-peri">{i + 1}</span>
            <span className="text-[14px] text-ink-2">{t}</span>
          </div>
        ))}
      </Card>

      {c.grades.length > 0 && (
        <Card className="p-4">
          <div className="text-[16px] font-bold text-ink">Darajalar (taxminiy)</div>
          <div className="mt-3 flex flex-wrap gap-2">
            {c.grades.map((g) => (
              <span key={g.grade} className="inline-flex items-baseline gap-1.5 rounded-xl bg-surface-2 px-3 py-1.5">
                <b className="text-[15px] text-ink">{g.grade}</b><span className="text-[12.5px] text-muted">{g.min_percent}%+</span>
              </span>
            ))}
          </div>
          <div className="mt-2 text-[12px] text-muted">Format rasmiy spetsifikatsiya e’lon qilingach moslashtiriladi.</div>
        </Card>
      )}

      {info.history.length > 0 && (
        <>
          <SectionTitle>Oldingi natijalar</SectionTitle>
          <Card className="divide-y divide-line overflow-hidden">
            {info.history.map((h) => (
              <div key={h.id} className="flex items-center gap-3 px-4 py-3">
                <span className="grid h-10 w-10 place-items-center rounded-xl bg-shaxs-soft text-[15px] font-extrabold text-shaxs">{h.grade}</span>
                <div className="min-w-0 flex-1">
                  <div className="text-[15px] font-bold tabular-nums text-ink">{h.score} / {c.max_score}</div>
                  <Bar value={h.score / c.max_score} className="mt-1 h-1.5" tone="bg-shaxs" />
                </div>
                <span className="text-[12.5px] text-muted">{new Date(h.date).toLocaleDateString()}</span>
              </div>
            ))}
          </Card>
        </>
      )}

      <button type="button" disabled={busy} onClick={onStart}
        className="w-full rounded-full bg-cta py-3.5 text-[16px] font-bold text-on-cta transition active:scale-[.99] disabled:opacity-60">
        {info.open_exam_id ? "Davom ettirish" : "Imtihonni boshlash"}
      </button>
    </Screen>
  );
}

function fmt(ms: number): string {
  const s = Math.max(0, Math.floor(ms / 1000));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  return (h ? `${h}:${String(m).padStart(2, "0")}` : `${m}`) + `:${String(sec).padStart(2, "0")}`;
}

function ExamRunner({ exam, onFinish }: { exam: Running; onFinish: (r: Result) => void }) {
  const { reload } = useStore();
  const [answers, setAnswers] = useState<Record<number, string>>(() =>
    Object.fromEntries(exam.questions.filter((q) => q.chosen).map((q) => [q.id, q.chosen!])));
  const [idx, setIdx] = useState(0);
  const [grid, setGrid] = useState(false);
  const offset = useMemo(() => new Date(exam.now).getTime() - Date.now(), [exam.now]);
  const deadline = useMemo(() => new Date(exam.deadline).getTime(), [exam.deadline]);
  const [left, setLeft] = useState(deadline - (Date.now() + offset));
  const finishing = useRef(false);

  const finish = useCallback(async () => {
    if (finishing.current) return;
    finishing.current = true;
    try {
      const r = await api<Result>(`/exam/${exam.id}/finish`, { method: "POST" });
      haptic.success();
      void reload();
      onFinish(r);
    } catch (e) {
      finishing.current = false;
      toast((e as Error).message, "error");
    }
  }, [exam.id, onFinish, reload]);

  useEffect(() => {
    const id = setInterval(() => {
      const l = deadline - (Date.now() + offset);
      setLeft(l);
      if (l <= 0) void finish();
    }, 500);
    return () => clearInterval(id);
  }, [deadline, offset, finish]);

  useEffect(() => {
    tg?.enableClosingConfirmation?.();
    return () => tg?.disableClosingConfirmation?.();
  }, []);

  const q = exam.questions[idx];
  const answered = Object.keys(answers).length;

  async function choose(key: string) {
    haptic.select();
    const prev = answers[q.id];
    setAnswers((a) => ({ ...a, [q.id]: key }));
    try {
      await api(`/exam/${exam.id}/answer`, { method: "PUT", body: { question_id: q.id, option: key } });
    } catch (e) {
      setAnswers((a) => { const c = { ...a }; if (prev) c[q.id] = prev; else delete c[q.id]; return c; });
      toast((e as Error).message, "error");
      if ((e as { status?: number }).status === 409) void finish();
    }
  }

  async function askFinish() {
    const rest = exam.questions.length - answered;
    const msg = rest > 0 ? `${rest} ta savolga javob berilmagan. Imtihonni yakunlaysizmi?` : "Imtihonni yakunlaysizmi?";
    if (await confirmDialog(msg)) void finish();
  }

  const warn = left < 5 * 60000;
  return (
    <div className="min-h-screen pb-[calc(var(--safe-bottom)+110px)]">
      <div className={cx(wrap, "sticky top-0 z-10 space-y-2 bg-canvas/90 pb-3 pt-[calc(var(--safe-top)+12px)] backdrop-blur")}>
        <div className="flex items-center gap-2">
          <button type="button" onClick={() => navigate("/", true)} aria-label="Chiqish"
            className="grid h-9 w-9 place-items-center rounded-full text-muted hover:bg-surface-2"><Close size={20} /></button>
          <span className={cx("inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[15px] font-extrabold tabular-nums",
            warn ? "animate-pulse bg-danger-soft text-danger" : "bg-surface text-ink shadow-soft")}>
            <Clock size={16} /> {fmt(left)}
          </span>
          <span className="flex-1" />
          <button type="button" onClick={() => setGrid(true)}
            className="rounded-full border border-line-strong bg-surface px-3 py-1.5 text-[13.5px] font-bold tabular-nums text-ink">
            {answered}/{exam.questions.length}
          </button>
          <button type="button" onClick={askFinish}
            className="rounded-full bg-cta px-3.5 py-1.5 text-[13.5px] font-bold text-on-cta">Yakunlash</button>
        </div>
        <Bar value={answered / exam.questions.length} className="h-1.5" tone="bg-shaxs" />
      </div>
      <div key={q.id} className={cx(wrap, "animate-page")}>
        <div className="mb-3 text-[12px] font-bold uppercase tracking-[.12em] text-muted">Savol {idx + 1} / {exam.questions.length}</div>
        <QuestionView q={q} selected={answers[q.id] ?? null} onSelect={choose} />
      </div>
      <div className="fixed inset-x-0 bottom-0 z-20 border-t border-line bg-surface/95 backdrop-blur">
        <div className={cx(wrap, "flex gap-3 py-3 pb-[calc(var(--safe-bottom)+12px)]")}>
          <button type="button" disabled={idx === 0} onClick={() => setIdx(idx - 1)} aria-label="Oldingi"
            className="grid w-14 place-items-center rounded-full border border-line-strong bg-surface text-ink disabled:opacity-40"><ChevronLeft /></button>
          {idx + 1 < exam.questions.length
            ? <button type="button" onClick={() => setIdx(idx + 1)}
                className="inline-flex flex-1 items-center justify-center gap-1 rounded-full bg-cta py-3.5 text-[16px] font-bold text-on-cta active:scale-[.99]">Keyingi <ChevronRight size={20} /></button>
            : <button type="button" onClick={askFinish}
                className="flex-1 rounded-full bg-cta py-3.5 text-[16px] font-bold text-on-cta active:scale-[.99]">Yakunlash</button>}
        </div>
      </div>
      {grid && (
        <Sheet onClose={() => setGrid(false)}>
          <div className="space-y-4">
            <h2 className="text-[20px] font-extrabold text-ink">Savollar</h2>
            <div className="grid grid-cols-6 gap-2">
              {exam.questions.map((qq, i) => (
                <button key={qq.id} type="button" onClick={() => { setIdx(i); setGrid(false); }}
                  className={cx("aspect-square rounded-xl border-2 text-[14px] font-bold tabular-nums transition",
                    answers[qq.id] ? "border-shaxs bg-shaxs-soft text-shaxs" : "border-line bg-surface text-muted",
                    i === idx && "ring-2 ring-peri ring-offset-2 ring-offset-surface")}>{i + 1}</button>
              ))}
            </div>
            <button type="button" onClick={askFinish} className="w-full rounded-full bg-cta py-3.5 text-[15px] font-bold text-on-cta">Imtihonni yakunlash</button>
          </div>
        </Sheet>
      )}
    </div>
  );
}

function ExamResult({ result, onDone }: { result: Result; onDone: () => void }) {
  const [open, setOpen] = useState<number | null>(null);
  const item = open !== null ? result.items[open] : null;
  const tone = result.percent >= 70 ? "var(--success)" : result.percent >= 40 ? "var(--accent)" : "var(--danger)";
  return (
    <div className={cx(wrap, "pt-[calc(var(--safe-top)+28px)] pb-[calc(var(--safe-bottom)+100px)]")}>
      <div className="stagger space-y-5">
        <div className="relative flex flex-col items-center text-center">
          {result.percent >= 70 && <Confetti />}
          <div className="text-[12px] font-bold uppercase tracking-[.14em] text-muted">Imtihon yakunlandi</div>
          <div className="mt-4 flex items-center gap-6">
            <ProgressRing value={result.percent / 100} size={148} stroke={12} tone={tone}>
              <div>
                <div className="text-[34px] font-extrabold leading-none tracking-tight text-ink">
                  {result.score % 1 ? result.score : <CountUp value={result.score} />}
                </div>
                <div className="mt-1 text-[12.5px] font-semibold text-muted">/ {result.max_score} ball</div>
              </div>
            </ProgressRing>
            <div className="flex flex-col items-center">
              <span className="grid h-20 w-20 animate-pop place-items-center rounded-[24px] bg-shaxs-soft text-[34px] font-extrabold text-shaxs [animation-delay:.5s]">{result.grade}</span>
              <span className="mt-1.5 text-[12.5px] font-semibold text-muted">daraja</span>
            </div>
          </div>
          <p className="mt-3 text-[12.5px] text-muted">Taxminiy natija — rasmiy shkala e’lon qilingach moslashtiriladi.</p>
        </div>

        <div className="grid grid-cols-3 gap-2.5">
          {[["To‘g‘ri", result.correct, "text-success"], ["Xato", result.total - result.correct, "text-danger"],
            ["Foiz", `${Math.round(result.percent)}%`, "text-ink"]].map(([l, v, c]) => (
            <div key={String(l)} className="rounded-2xl border border-line bg-surface px-3 py-3 text-center shadow-soft">
              <div className="text-[12px] font-semibold text-muted">{l}</div>
              <div className={cx("mt-0.5 text-[22px] font-extrabold tabular-nums", String(c))}>{v}</div>
            </div>
          ))}
        </div>

        <Card className="space-y-3 p-4">
          <div className="text-[16px] font-bold text-ink">Savollar tahlili</div>
          <div className="stagger grid grid-cols-6 gap-2">
            {result.items.map((it, i) => (
              <button key={it.id} type="button" onClick={() => setOpen(i)}
                className={cx("aspect-square rounded-xl text-[14px] font-bold tabular-nums transition active:scale-95",
                  it.is_correct ? "bg-success-soft text-success" : "bg-danger-soft text-danger")}>{i + 1}</button>
            ))}
          </div>
          <div className="text-[12.5px] text-muted">Raqamni bosib, izohni ko‘ring. Xato javoblar takrorlash bo‘limiga qo‘shildi.</div>
        </Card>
      </div>

      <div className="fixed inset-x-0 bottom-0 z-20 border-t border-line bg-surface/95 backdrop-blur">
        <div className={cx(wrap, "py-3 pb-[calc(var(--safe-bottom)+12px)]")}>
          <button type="button" onClick={onDone}
            className="w-full rounded-full bg-cta py-3.5 text-[16px] font-bold text-on-cta active:scale-[.99]">Davom etish</button>
        </div>
      </div>
      {item && (
        <Sheet onClose={() => setOpen(null)}>
          <div className="space-y-4">
            <QuestionView q={item} selected={item.chosen || null} correct={item.correct_option} locked onSelect={() => {}} />
            {!item.chosen && <Pill className="bg-danger-soft text-danger">Javob berilmagan</Pill>}
            {item.explanation && (
              <div className="rounded-2xl bg-surface-2/70 p-3.5">
                <div className="text-[12px] font-bold uppercase tracking-[.1em] text-muted">Izoh</div>
                <p className="mt-1 font-reading text-[15px] leading-relaxed text-ink-2">{item.explanation}</p>
              </div>
            )}
            <button type="button" onClick={() => setOpen(null)}
              className="w-full rounded-full border border-line-strong bg-surface py-3.5 text-[15px] font-bold text-ink">Yopish</button>
          </div>
        </Sheet>
      )}
    </div>
  );
}
