import { useEffect, useRef, useState } from "react";
import { Check, Close, Cross, Flag, Flame, Refresh } from "../components/Icons";
import { CountUp } from "../components/CountUp";
import { QuestionView } from "../components/QuestionView";
import { ReportSheet } from "../components/ReportSheet";
import { Loading, Progress, toast } from "../components/ui";
import { api } from "../lib/api";
import { navigate } from "../lib/router";
import { useStore } from "../lib/store";
import { confirmDialog, haptic } from "../lib/telegram";
import type { AnswerResult, Question } from "../lib/types";

type Mode = "daily" | "review" | "mixed" | "period" | "topic";
const PRAISE = ["To'g'ri", "To'g'ri javob", "Aynan shunday"];

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

  useEffect(() => {
    api<{ lesson_id: number; source: string; questions: Question[] }>("/lessons", { body: { mode, id } })
      .then((r) => { setQuestions(r.questions); setSource(r.source); setLessonId(r.lesson_id); })
      .catch((e) => { toast(e.message, "error"); setQuestions([]); });
  }, [mode, id]);

  if (!questions) return <Loading />;

  if (questions.length === 0) {
    return (
      <div className="page no-nav">
        <div className="empty" style={{ minHeight: "70vh", justifyContent: "center" }}>
          <span className="empty-icon"><Refresh size={26} /></span>
          <h2>{mode === "review" ? "Takrorlash uchun savol yo'q" : "Bu bo'limda savol yo'q"}</h2>
          <p className="muted">
            {mode === "review"
              ? "Xato javob bergan savollaringiz shu yerga tushadi va 1, 2, 4, 7, 15, 30 kunlik oraliqlarda qayta beriladi."
              : "Tez orada savollar qo'shiladi."}
          </p>
          <button className="btn block" onClick={() => navigate("/", true)}>Bosh sahifa</button>
        </div>
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
    const accuracy = Math.round((stats.correct / total) * 100);
    const wrong = total - stats.correct;
    return (
      <div className="page no-nav stack">
        <div className="result-hero rise">
          <div className="eyebrow">Dars yakunlandi</div>
          <div className="result-score"><CountUp value={stats.correct} /><small> / {total}</small></div>
          <p className="muted">
            {accuracy >= 80 ? "A'lo natija. Bilimingiz mustahkam."
              : accuracy >= 50 ? "Yaxshi natija. Xato savollar takrorlashga qo'shildi."
              : `${wrong} ta xato savol takrorlash bo'limiga qo'shildi — ularni qayta ishlang.`}
          </p>
        </div>
        <div className="tiles rise">
          <div className="tile"><div className="label">Aniqlik</div><div className="value"><CountUp value={accuracy} suffix="%" /></div></div>
          <div className="tile gold"><div className="label">XP</div><div className="value">+<CountUp value={stats.xp} /></div></div>
          <div className="tile"><div className="label">Vaqt</div><div className="value">{Math.floor(seconds / 60)}:{String(seconds % 60).padStart(2, "0")}</div></div>
        </div>
        {(stats.goal || stats.streakUp) && (
          <div className="card row rise">
            <span className="icon-box accent"><Flame size={20} /></span>
            <div>
              <div className="bold">{stats.streak} kun ketma-ket</div>
              <div className="small muted">{stats.goal ? "Bugungi maqsad bajarildi" : "Ertaga ham davom ettiring"}</div>
            </div>
          </div>
        )}
        <div className="footer-bar"><div className="inner">
          <button className="btn block" onClick={() => navigate("/", true)}>Davom etish</button>
        </div></div>
      </div>
    );
  }

  return (
    <div>
      <div className="lesson-top">
        <button className="icon-btn" onClick={quit} aria-label="Yopish"><Close size={22} /></button>
        <div className="grow"><Progress value={(idx + (result ? 1 : 0)) / total} /></div>
        {stats.combo >= 3 && <span className="combo"><Flame size={14} />{stats.combo}</span>}
        <span className="count">{idx + 1}/{total}</span>
      </div>
      {/* Izoh oynasi ochiq bo'lsa, pastki variantlarni surib ko'rish uchun joy qoldiramiz */}
      <div className="page no-nav" style={{ paddingTop: 4, paddingBottom: result ? "min(60vh, 420px)" : undefined }}>
        <div className="eyebrow" style={{ marginBottom: 10 }}>
          {source === "review" ? "Takrorlash" : source === "daily" ? "Kunlik mashq" : "Mashq"}
        </div>
        <QuestionView q={q} selected={selected} correct={result?.correct_option} locked={!!result || busy}
          onSelect={(k) => { haptic.select(); setSelected(k); }} />
      </div>

      {!result ? (
        <div className="footer-bar"><div className="inner">
          <button className="btn block" disabled={!selected || busy} onClick={check}>Tekshirish</button>
        </div></div>
      ) : (
        <div className={`feedback ${result.is_correct ? "ok" : "bad"}`}>
          <div className="inner">
            <div className="row between">
              <h3>
                {result.is_correct ? <Check size={22} /> : <Cross size={22} />}
                {result.is_correct ? PRAISE[idx % PRAISE.length] : "Noto'g'ri"}
              </h3>
              <button className="icon-btn" onClick={() => setReport(true)} aria-label="Xato bor" title="Xato bor">
                <Flag size={18} />
              </button>
            </div>
            {!result.is_correct && (
              <div className="answer">
                To'g'ri javob: {result.correct_option.toUpperCase()}) {q.options.find((o) => o.key === result.correct_option)?.text}
              </div>
            )}
            {result.explanation && (
              <div className="explain"><b>Izoh</b>{result.explanation}</div>
            )}
            <button className="btn block" onClick={next}>
              {idx + 1 >= total ? "Yakunlash" : "Davom etish"}
            </button>
          </div>
        </div>
      )}
      {report && <ReportSheet questionId={q.id} onClose={() => setReport(false)} />}
    </div>
  );
}
