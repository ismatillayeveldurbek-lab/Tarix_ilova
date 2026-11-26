import { useEffect, useRef, useState } from "react";
import { Check, Close, Cross, Flag, Flame, Refresh } from "../components/Icons";
import { CountUp } from "../components/CountUp";
import { Bar, Pill, cx } from "../components/kit";
import { Confetti, FloatUp, ProgressRing } from "../components/motion";
import { QuestionView } from "../components/QuestionView";
import { ReportSheet } from "../components/ReportSheet";
import { Loading, toast } from "../components/ui";
import { api } from "../lib/api";
import { navigate } from "../lib/router";
import { useStore } from "../lib/store";
import { confirmDialog, haptic } from "../lib/telegram";
import type { AnswerResult, Question } from "../lib/types";

type Mode = "daily" | "review" | "mixed" | "period" | "topic";
const PRAISE = ["To‘g‘ri!", "Aynan shunday!", "Barakalla!", "Zo‘r!"];
const wrap = "mx-auto max-w-[560px] px-4";

function useHideNav() {
  useEffect(() => {
    document.body.classList.add("hide-nav");
    return () => document.body.classList.remove("hide-nav");
  }, []);
}

export function LessonPage({ mode, id }: { mode: Mode; id: number | null }) {
  const { reload } = useStore();
  const [questions, setQuestions] = useState<Question[] | null>(null);
  const [source, setSource] = useState("practice");
  const [lessonId, setLessonId] = useState(0);
  const [idx, setIdx] = useState(0);
  const [selected, setSelected] = useState<string | null>(null);
  const [result, setResult] = useState<AnswerResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [report, setReport] = useState(false);
  const [stats, setStats] = useState({ correct: 0, xp: 0, combo: 0, best: 0, goal: false, streakUp: false, streak: 0 });
  const [finished, setFinished] = useState(false);
  const started = useRef(Date.now());
  useHideNav();

  useEffect(() => {
    api<{ lesson_id: number; source: string; questions: Question[] }>("/lessons", { body: { mode, id } })
      .then((r) => { setQuestions(r.questions); setSource(r.source); setLessonId(r.lesson_id); })
      .catch((e) => { toast(e.message, "error"); setQuestions([]); });
  }, [mode, id]);

  if (!questions) return <Loading />;

  if (questions.length === 0) {
    return (
      <div className={cx(wrap, "flex min-h-screen flex-col items-center justify-center gap-4 text-center")}>
        <span className="grid h-16 w-16 animate-pop place-items-center rounded-[20px] bg-peri-soft text-peri"><Refresh size={28} /></span>
        <h1 className="text-[22px] font-extrabold tracking-tight text-ink">
          {mode === "review" ? "Takrorlash uchun savol yo‘q" : "Bu bo‘limda savol yo‘q"}
        </h1>
        <p className="max-w-[340px] text-[15px] text-muted">
          {mode === "review"
            ? "Xato javob bergan savollaringiz shu yerga tushadi va 1, 2, 4, 7, 15, 30 kunlik oraliqlarda qayta beriladi."
            : "Tez orada savollar qo‘shiladi."}
        </p>
        <button type="button" onClick={() => navigate("/", true)}
          className="mt-2 w-full max-w-[360px] rounded-full bg-cta py-3.5 text-[15px] font-bold text-on-cta">Bosh sahifa</button>
      </div>
    );
  }

  const q = questions[idx];
  const total = questions.length;

  async function check() {
    if (!selected || busy) return;
    setBusy(true);
    try {
      const r = await api<AnswerResult>("/answers", { body: { lesson_id: lessonId, question_id: q.id, option: selected } });
      setResult(r);
      if (r.is_correct) haptic.success(); else haptic.error();
      if (r.referral_bonus) toast(`Taklif bonusi: +${r.referral_bonus} XP`, "success");
      setStats((s) => {
        const combo = r.is_correct ? s.combo + 1 : 0;
        return {
          correct: s.correct + (r.is_correct ? 1 : 0), xp: s.xp + r.xp + r.referral_bonus, combo, best: Math.max(s.best, combo),
          goal: s.goal || r.goal_reached, streakUp: s.streakUp || r.streak_increased, streak: r.streak,
        };
      });
    } catch (e) {
      toast((e as Error).message, "error");
    } finally {
      setBusy(false);
    }
  }

  function next() {
    haptic.tap();
    if (idx + 1 >= total) {
      setFinished(true);
      void reload();
      return;
    }
    setIdx(idx + 1);
    setSelected(null);
    setResult(null);
    window.scrollTo(0, 0);
  }

  async function quit() {
    if (idx === 0 && !result) return navigate("/", true);
    if (await confirmDialog("Darsni tugatasizmi? Berilgan javoblar saqlanadi.")) {
      void reload();
      navigate("/", true);
    }
  }

  if (finished) {
    const seconds = Math.round((Date.now() - started.current) / 1000);
    return <LessonResult total={total} stats={stats} seconds={seconds} />;
  }

  const ok = result?.is_correct;
  return (
    <div className="min-h-screen pb-[calc(var(--safe-bottom)+120px)]">
      {/* Yuqori panel */}
      <div className={cx(wrap, "sticky top-0 z-10 flex items-center gap-3 bg-canvas/90 pb-3 pt-[calc(var(--safe-top)+12px)] backdrop-blur")}>
        <button type="button" onClick={quit} aria-label="Yopish" className="grid h-9 w-9 place-items-center rounded-full text-muted hover:bg-surface-2">
          <Close size={20} />
        </button>
        <Bar value={(idx + (result ? 1 : 0)) / total} className="h-2.5 flex-1" tone={ok === false ? "bg-danger" : "bg-success"} />
        {stats.combo >= 2 && (
          <span key={stats.combo} className="inline-flex animate-pop items-center gap-0.5 rounded-full bg-peach-soft px-2 py-0.5 text-[13px] font-bold text-peach">
            <Flame size={14} />{stats.combo}
          </span>
        )}
        <span className="text-[13px] font-bold tabular-nums text-muted">{idx + 1}/{total}</span>
      </div>

      <div key={q.id} className={cx(wrap, "animate-page")}
        style={{ paddingBottom: result ? "min(52vh, 380px)" : undefined }}>
        <div className="mb-3 text-[12px] font-bold uppercase tracking-[.12em] text-muted">
          {source === "review" ? "Takrorlash" : source === "daily" ? "Kunlik test" : "Mashq"}
        </div>
        <QuestionView q={q} selected={selected} correct={result?.correct_option} locked={!!result || busy}
          onSelect={(k) => { haptic.select(); setSelected(k); }} />
      </div>

      {!result ? (
        <div className="fixed inset-x-0 bottom-0 z-20 border-t border-line bg-surface/95 backdrop-blur">
          <div className={cx(wrap, "py-3 pb-[calc(var(--safe-bottom)+12px)]")}>
            <button type="button" disabled={!selected || busy} onClick={check}
              className="w-full rounded-full bg-cta py-3.5 text-[16px] font-bold text-on-cta transition active:scale-[.99] disabled:opacity-40">
              Tekshirish
            </button>
          </div>
        </div>
      ) : (
        <div className={cx("fixed inset-x-0 bottom-0 z-20 animate-sheet-up rounded-t-[28px] border-t-2 shadow-lift",
          ok ? "border-success bg-success-soft" : "border-danger bg-danger-soft")}>
          <div className={cx(wrap, "relative max-h-[60vh] overflow-y-auto pt-5 pb-[calc(var(--safe-bottom)+14px)]")}>
            {ok && result.xp > 0 && <FloatUp className="right-6 top-2 text-success">+{result.xp} XP</FloatUp>}
            <div className="flex items-center justify-between">
              <h3 className={cx("flex items-center gap-2 text-[21px] font-extrabold tracking-tight", ok ? "text-success" : "text-danger")}>
                <span className={cx("grid h-9 w-9 animate-pop place-items-center rounded-full", ok ? "bg-success text-on-success" : "bg-danger text-white")}>
                  {ok ? <Check size={20} /> : <Cross size={20} />}
                </span>
                {ok ? PRAISE[idx % PRAISE.length] : "Noto‘g‘ri"}
              </h3>
              <button type="button" onClick={() => setReport(true)} aria-label="Xato bor" title="Xato bor"
                className="grid h-9 w-9 place-items-center rounded-full text-muted hover:bg-black/5">
                <Flag size={18} />
              </button>
            </div>
            {!ok && (
              <div className="mt-3 text-[15px] font-semibold text-ink">
                To‘g‘ri javob: <span className="text-success">{result.correct_option.toUpperCase()}) {q.options.find((o) => o.key === result.correct_option)?.text}</span>
              </div>
            )}
            {result.explanation && (
              <p className="mt-2.5 font-reading text-[15.5px] leading-relaxed text-ink-2">{result.explanation}</p>
            )}
            {!ok && <p className="mt-2 text-[12.5px] text-muted">Bu savol takrorlash ro‘yxatiga qo‘shildi.</p>}
            <button type="button" onClick={next}
              className={cx("mt-4 w-full rounded-full py-3.5 text-[16px] font-bold transition active:scale-[.99]",
                ok ? "bg-success text-on-success" : "bg-danger text-white")}>
              {idx + 1 >= total ? "Natijani ko‘rish" : "Davom etish"}
            </button>
          </div>
        </div>
      )}
      {report && <ReportSheet questionId={q.id} onClose={() => setReport(false)} />}
    </div>
  );
}

function LessonResult({ total, seconds, stats }: {
  total: number; seconds: number;
  stats: { correct: number; xp: number; best: number; goal: boolean; streakUp: boolean; streak: number };
}) {
  const accuracy = Math.round((stats.correct / total) * 100);
  const wrong = total - stats.correct;
  const tone = accuracy >= 80 ? "var(--success)" : accuracy >= 50 ? "var(--accent)" : "var(--danger)";
  return (
    <div className={cx(wrap, "flex min-h-screen flex-col pt-[calc(var(--safe-top)+28px)] pb-[calc(var(--safe-bottom)+100px)]")}>
      <div className="stagger space-y-5">
        <div className="relative flex flex-col items-center text-center">
          {accuracy >= 80 && <Confetti />}
          <div className="text-[12px] font-bold uppercase tracking-[.14em] text-muted">Dars yakunlandi</div>
          <div className="mt-4">
            <ProgressRing value={stats.correct / total} size={156} stroke={12} tone={tone}>
              <div>
                <div className="text-[40px] font-extrabold leading-none tracking-tight text-ink"><CountUp value={stats.correct} /></div>
                <div className="mt-1 text-[13px] font-semibold text-muted">/ {total} to‘g‘ri</div>
              </div>
            </ProgressRing>
          </div>
          <p className="mt-4 max-w-[340px] text-[15px] text-muted">
            {accuracy >= 80 ? "A’lo natija. Bilimingiz mustahkam."
              : accuracy >= 50 ? "Yaxshi natija. Xato savollar takrorlashga qo‘shildi."
              : `${wrong} ta xato savol takrorlash bo‘limiga qo‘shildi — ularni qayta ishlang.`}
          </p>
        </div>

        <div className="grid grid-cols-3 gap-2.5">
          {[
            { label: "Aniqlik", value: <><CountUp value={accuracy} />%</>, cls: "text-ink" },
            { label: "XP", value: <>+<CountUp value={stats.xp} /></>, cls: "text-peach" },
            { label: "Vaqt", value: `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`, cls: "text-ink" },
          ].map((t) => (
            <div key={t.label} className="rounded-2xl border border-line bg-surface px-3 py-3 text-center shadow-soft">
              <div className="text-[12px] font-semibold text-muted">{t.label}</div>
              <div className={cx("mt-0.5 text-[22px] font-extrabold tabular-nums", t.cls)}>{t.value}</div>
            </div>
          ))}
        </div>

        {stats.best >= 3 && (
          <div className="flex items-center justify-center gap-2 text-[14px] font-semibold text-muted">
            <Pill className="bg-peach-soft text-peach"><Flame size={13} />{stats.best}</Pill> ketma-ket to‘g‘ri javob — eng yaxshi seriya
          </div>
        )}

        {(stats.goal || stats.streakUp) && (
          <div className="flex items-center gap-3 rounded-card border border-line bg-surface p-4 shadow-soft">
            <span className="grid h-12 w-12 place-items-center rounded-2xl bg-peach-soft text-peach">
              <Flame size={24} className="animate-breathe" />
            </span>
            <div>
              <div className="text-[16px] font-bold text-ink">{stats.streak} kun ketma-ket</div>
              <div className="text-[13px] text-muted">{stats.goal ? "Bugungi maqsad bajarildi" : "Ertaga ham davom ettiring"}</div>
            </div>
          </div>
        )}
      </div>

      <div className="fixed inset-x-0 bottom-0 z-20 border-t border-line bg-surface/95 backdrop-blur">
        <div className={cx(wrap, "py-3 pb-[calc(var(--safe-bottom)+12px)]")}>
          <button type="button" onClick={() => navigate("/", true)}
            className="w-full rounded-full bg-cta py-3.5 text-[16px] font-bold text-on-cta transition active:scale-[.99]">Davom etish</button>
        </div>
      </div>
    </div>
  );
}
