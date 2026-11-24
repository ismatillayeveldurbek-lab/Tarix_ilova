import { useEffect, useRef, useState } from "react";
import { Check, Close, Cross, Flag, Flame, Star } from "../components/Icons";
import { Mascot } from "../components/Mascot";
import { QuestionView } from "../components/QuestionView";
import { ReportSheet } from "../components/ReportSheet";
import { Loading, Progress, toast } from "../components/ui";
import { api } from "../lib/api";
import { navigate } from "../lib/router";
import { useStore } from "../lib/store";
import { confirmDialog, haptic } from "../lib/telegram";
import type { AnswerResult, Question } from "../lib/types";

type Mode = "daily" | "review" | "mixed" | "period" | "topic";
const PRAISE = ["Barakalla!", "Zo'r!", "Ajoyib!", "To'ppa-to'g'ri!", "Qoyil!"];

export function LessonPage({ mode, id }: { mode: Mode; id: number | null }) {
  const { t, reload } = useStore();
  const [questions, setQuestions] = useState<Question[] | null>(null);
  const [source, setSource] = useState("practice");
  const [idx, setIdx] = useState(0);
  const [selected, setSelected] = useState<string | null>(null);
  const [result, setResult] = useState<AnswerResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [report, setReport] = useState(false);
  const [stats, setStats] = useState({ correct: 0, xp: 0, combo: 0, best: 0, goal: false, streakUp: false, streak: 0 });
  const [finished, setFinished] = useState(false);
  const started = useRef(Date.now());

  useEffect(() => {
    api<{ source: string; questions: Question[] }>("/lessons", { body: { mode, id } })
      .then((r) => { setQuestions(r.questions); setSource(r.source); })
      .catch((e) => { toast(e.message, "error"); setQuestions([]); });
  }, [mode, id]);

  if (!questions) return <Loading />;

  if (questions.length === 0) {
    return (
      <div className="page no-nav">
        <div className="empty" style={{ minHeight: "70vh", justifyContent: "center" }}>
          <Mascot mood={mode === "review" ? "wow" : "think"} size={140} className="bob" />
          <h2>{mode === "review" ? t("Takrorlash uchun savol yo'q!") : t("Bu bo'limda savol yo'q")}</h2>
          <p className="muted">
            {mode === "review"
              ? t("Xato javob bergan savollaringiz shu yerga tushadi va 1, 2, 4, 7, 15, 30 kunlik oraliqlarda qayta beriladi.")
              : t("Tez orada savollar qo'shiladi.")}
          </p>
          <button className="btn block" onClick={() => navigate("/", true)}>{t("Bosh sahifa")}</button>
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
      const r = await api<AnswerResult>("/answers", { body: { question_id: q.id, option: selected, source } });
      setResult(r);
      if (r.is_correct) haptic.success(); else haptic.error();
      setStats((s) => {
        const combo = r.is_correct ? s.combo + 1 : 0;
        return {
          correct: s.correct + (r.is_correct ? 1 : 0), xp: s.xp + r.xp, combo, best: Math.max(s.best, combo),
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
    if (await confirmDialog(t("Darsni tugatasizmi? Berilgan javoblar saqlanadi."))) {
      void reload();
      navigate("/", true);
    }
  }

  if (finished) {
    const seconds = Math.round((Date.now() - started.current) / 1000);
    const accuracy = Math.round((stats.correct / total) * 100);
    const mood = accuracy >= 70 ? "wow" : accuracy >= 40 ? "happy" : "sad";
    return (
      <div className="page no-nav">
        <div className="result-hero">
          <Mascot mood={mood} size={150} className="pop" />
          <h1 className="pop">{accuracy >= 70 ? t("Dars yakunlandi!") : t("Yaxshi harakat!")}</h1>
          <p className="muted">
            {accuracy >= 70 ? t("Bilimingiz mustahkamlanmoqda. Shu zaylda davom eting!") : t("Xatolar ustida ishlash bo'limida ularni qayta mashq qiling.")}
          </p>
        </div>
        <div className="tiles">
          <div className="tile gold pop"><div className="label">{t("Jami XP")}</div><div className="value"><Star size={22} />{stats.xp}</div></div>
          <div className="tile green pop"><div className="label">{t("Aniqlik")}</div><div className="value">{accuracy}%</div></div>
          <div className="tile blue pop"><div className="label">{t("Vaqt")}</div><div className="value">{Math.floor(seconds / 60)}:{String(seconds % 60).padStart(2, "0")}</div></div>
        </div>
        <div className="spacer" />
        {(stats.goal || stats.streakUp) && (
          <div className="card colored orange feature pop">
            <div className="icon-bubble"><Flame size={34} /></div>
            <div>
              <h3>{t(`${stats.streak} kun ketma-ket!`)}</h3>
              <div className="small muted">{stats.goal ? t("Bugungi maqsad bajarildi 🎉") : t("Ertaga ham qaytib keling!")}</div>
            </div>
          </div>
        )}
        <div className="footer-bar"><div className="inner">
          <button className="btn block" onClick={() => navigate("/", true)}>{t("Davom etish")}</button>
        </div></div>
      </div>
    );
  }

  return (
    <div>
      <div className="lesson-top">
        <button className="icon-btn" onClick={quit} aria-label="Yopish"><Close size={28} /></button>
        <div className="grow"><Progress value={(idx + (result ? 1 : 0)) / total} /></div>
        {stats.combo >= 2 && <span className="combo pop">🔥 {stats.combo}</span>}
      </div>
      <div className="page no-nav" style={{ paddingTop: 4 }}>
        <div className="small muted bold" style={{ marginBottom: 8 }}>
          {source === "review" ? t("Takrorlash") : source === "daily" ? t("Kunlik mashq") : t("Mashq")} · {idx + 1}/{total}
        </div>
        <QuestionView q={q} selected={selected} correct={result?.correct_option} locked={!!result || busy}
          onSelect={(k) => { haptic.select(); setSelected(k); }} />
      </div>

      {!result ? (
        <div className="footer-bar"><div className="inner">
          <button className="btn block" disabled={!selected || busy} onClick={check}>{t("Tekshirish")}</button>
        </div></div>
      ) : (
        <div className={`feedback ${result.is_correct ? "ok" : "bad"}`}>
          <div className="inner">
            <div className="row between">
              <h3>
                {result.is_correct ? <Check size={30} /> : <Cross size={30} />}
                {result.is_correct ? t(PRAISE[idx % PRAISE.length]) : t("Noto'g'ri")}
              </h3>
              <button className="icon-btn" onClick={() => setReport(true)} aria-label={t("Xato bor")} title={t("Xato bor")}>
                <Flag size={22} />
              </button>
            </div>
            {!result.is_correct && (
              <div className="bold" style={{ color: "var(--red)" }}>
                {t("To'g'ri javob")}: {result.correct_option.toUpperCase()}) {q.options.find((o) => o.key === result.correct_option)?.text}
              </div>
            )}
            {result.explanation && (
              <div className="explain"><b>💡 {t("Izoh")}</b>{result.explanation}</div>
            )}
            <button className={`btn block ${result.is_correct ? "" : "red"}`} onClick={next}>
              {idx + 1 >= total ? t("Yakunlash") : t("Davom etish")}
            </button>
          </div>
        </div>
      )}
      {report && <ReportSheet questionId={q.id} onClose={() => setReport(false)} />}
    </div>
  );
}
