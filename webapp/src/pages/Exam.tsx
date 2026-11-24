import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ChevronLeft, ChevronRight, Clipboard, Clock, Close } from "../components/Icons";
import { Confetti } from "../components/Confetti";
import { CountUp } from "../components/CountUp";
import { Mascot } from "../components/Mascot";
import { QuestionView } from "../components/QuestionView";
import { Loading, Ring, Sheet, toast } from "../components/ui";
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

  // Imtihon va natija ekranida pastki menyu yashiriladi (tugmalarni to'smasin)
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
  const { t } = useStore();
  const c = info.config;
  if (!c) {
    return <div className="page"><div className="empty"><Mascot mood="think" /><p className="muted">{t("Imtihon formati hali sozlanmagan.")}</p></div></div>;
  }
  return (
    <div className="page stack">
      <div className="card colored purple" style={{ textAlign: "center", padding: 24 }}>
        <div style={{ display: "grid", placeItems: "center", marginBottom: 8 }}><Clipboard size={44} /></div>
        <h1 style={{ fontSize: 24 }}>{c.name}</h1>
        <div className="row" style={{ justifyContent: "center", gap: 16, marginTop: 12, fontWeight: 800 }}>
          <span>📝 {t(`${c.count} ta savol`)}</span>
          <span>⏱ {t(`${c.minutes} daqiqa`)}</span>
          <span>🏅 {t(`${c.max_score} ball`)}</span>
        </div>
      </div>
      <div className="card stack" style={{ gap: 6 }}>
        <div className="bold">{t("Qoidalar")}</div>
        <div className="small muted">• {t("Taymer boshlangach to'xtamaydi. Vaqt tugasa, imtihon avtomatik yakunlanadi.")}</div>
        <div className="small muted">• {t("Javoblar darhol saqlanadi — ilovani yopsangiz, qaytib davom ettira olasiz.")}</div>
        <div className="small muted">• {t("Savollar orasida bemalol o'tishingiz mumkin. Izohlar imtihon oxirida ko'rsatiladi.")}</div>
      </div>
      {c.grades.length > 0 && (
        <div className="card">
          <div className="bold" style={{ marginBottom: 6 }}>{t("Darajalar (taxminiy)")}</div>
          <table className="grades"><tbody>
            {c.grades.map((g) => (
              <tr key={g.grade}><td><span className="chip purple">{g.grade}</span></td><td className="muted">{t(`${g.min_percent}% va undan yuqori`)}</td></tr>
            ))}
          </tbody></table>
          <div className="tiny muted" style={{ marginTop: 8 }}>{t("Format rasmiy spetsifikatsiya e'lon qilingach moslashtiriladi.")}</div>
        </div>
      )}
      {info.history.length > 0 && (
        <div className="card">
          <div className="bold" style={{ marginBottom: 6 }}>{t("Oldingi natijalar")}</div>
          <div className="list">
            {info.history.map((h) => (
              <div key={h.id} className="list-row">
                <span className="chip purple">{h.grade}</span>
                <span className="grow bold">{h.score} / {c.max_score}</span>
                <span className="small muted">{new Date(h.date).toLocaleDateString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      <button className="btn purple block" disabled={busy} onClick={onStart}>
        {info.open_exam_id ? t("Davom ettirish") : t("Imtihonni boshlash")}
      </button>
    </div>
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
  const { t, reload } = useStore();
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
    const msg = rest > 0 ? t(`${rest} ta savolga javob berilmagan. Imtihonni yakunlaysizmi?`) : t("Imtihonni yakunlaysizmi?");
    if (await confirmDialog(msg)) void finish();
  }

  return (
    <div>
      <div className="lesson-top" style={{ borderBottom: "2px solid var(--border)" }}>
        <button className="icon-btn" onClick={() => navigate("/", true)} aria-label="Chiqish"><Close size={26} /></button>
        <span className={`timer ${left < 5 * 60000 ? "warn" : ""}`}><Clock size={20} />{fmt(left)}</span>
        <div className="grow" />
        <button className="btn sm white" onClick={() => setGrid(true)}>{answered}/{exam.questions.length}</button>
        <button className="btn sm purple" onClick={askFinish}>{t("Yakunlash")}</button>
      </div>
      <div className="page no-nav">
        <div className="small muted bold" style={{ marginBottom: 8 }}>{t("Savol")} {idx + 1} / {exam.questions.length}</div>
        <QuestionView q={q} selected={answers[q.id] ?? null} onSelect={choose} />
      </div>
      <div className="footer-bar"><div className="inner row">
        <button className="btn white" disabled={idx === 0} onClick={() => setIdx(idx - 1)}><ChevronLeft /></button>
        {idx + 1 < exam.questions.length
          ? <button className="btn purple grow" onClick={() => setIdx(idx + 1)}>{t("Keyingi")} <ChevronRight size={20} /></button>
          : <button className="btn grow" onClick={askFinish}>{t("Yakunlash")}</button>}
      </div></div>
      {grid && (
        <Sheet onClose={() => setGrid(false)}>
          <div className="stack">
            <h2 style={{ fontSize: 20 }}>{t("Savollar")}</h2>
            <div className="q-grid">
              {exam.questions.map((qq, i) => (
                <button key={qq.id} className={`${answers[qq.id] ? "answered" : ""} ${i === idx ? "current" : ""}`}
                  onClick={() => { setIdx(i); setGrid(false); }}>{i + 1}</button>
              ))}
            </div>
            <button className="btn purple block" onClick={askFinish}>{t("Imtihonni yakunlash")}</button>
          </div>
        </Sheet>
      )}
    </div>
  );
}

function ExamResult({ result, onDone }: { result: Result; onDone: () => void }) {
  const { t } = useStore();
  const [open, setOpen] = useState<number | null>(null);
  const item = open !== null ? result.items[open] : null;
  return (
    <div className="page no-nav stack">
      <Confetti run={result.percent >= 50} />
      <div className="result-hero">
        <div className="grade-badge pop">{result.grade}</div>
        <h1 style={{ color: "var(--purple)" }}>{t("Imtihon yakunlandi!")}</h1>
        <p className="muted">{t("Bu taxminiy natija — rasmiy shkala e'lon qilingach moslashtiriladi.")}</p>
      </div>
      <div className="row" style={{ justifyContent: "center" }}>
        <Ring value={result.percent / 100} size={150} stroke={14} color="var(--purple)">
          <div className="center">
            <div style={{ fontSize: 30, fontWeight: 900 }}>{result.score % 1 ? result.score : <CountUp value={result.score} />}</div>
            <div className="small muted">/ {result.max_score} {t("ball")}</div>
          </div>
        </Ring>
      </div>
      <div className="tiles">
        <div className="tile green"><div className="label">{t("To'g'ri")}</div><div className="value">{result.correct}</div></div>
        <div className="tile red"><div className="label">{t("Xato")}</div><div className="value">{result.total - result.correct}</div></div>
        <div className="tile purple"><div className="label">{t("Foiz")}</div><div className="value">{Math.round(result.percent)}%</div></div>
      </div>
      <div className="card stack">
        <div className="bold">{t("Savollar tahlili")}</div>
        <div className="q-grid">
          {result.items.map((it, i) => (
            <button key={it.id} className={it.is_correct ? "ok" : "bad"} onClick={() => setOpen(i)}>{i + 1}</button>
          ))}
        </div>
        <div className="tiny muted">{t("Raqamni bosib, izohni ko'ring. Xato javoblar takrorlash bo'limiga qo'shildi.")}</div>
      </div>
      <div className="footer-bar"><div className="inner">
        <button className="btn purple block" onClick={onDone}>{t("Davom etish")}</button>
      </div></div>
      {item && (
        <Sheet onClose={() => setOpen(null)}>
          <div className="stack">
            <QuestionView q={item} selected={item.chosen || null} correct={item.correct_option} locked onSelect={() => {}} />
            {!item.chosen && <div className="chip red">{t("Javob berilmagan")}</div>}
            {item.explanation && <div className="card"><b>💡 {t("Izoh")}</b><div>{item.explanation}</div></div>}
            <button className="btn block white" onClick={() => setOpen(null)}>{t("Yopish")}</button>
          </div>
        </Sheet>
      )}
    </div>
  );
}
