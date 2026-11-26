import { useEffect, useState } from "react";
import { Plus, Trash } from "../../components/Icons";
import { Loading, toast } from "../../components/ui";
import { api } from "../../lib/api";
import { DIFFICULTY, usePeriods } from "./shared";

type Rule = { count: number; points: number; difficulty?: number | null; period?: string | null; topic?: string | null };
type Grade = { min_percent: number; grade: string };
type Config = { name: string; duration_minutes: number; max_score: number; rules: Rule[]; grades: Grade[]; availability?: number[] };

const DEFAULT: Config = {
  name: "Sinov imtihoni", duration_minutes: 60, max_score: 100,
  rules: [{ count: 10, points: 1 }], grades: [{ min_percent: 70, grade: "A" }, { min_percent: 50, grade: "B" }],
};

export function ExamConfigPage() {
  const { periods } = usePeriods();
  const [c, setC] = useState<Config | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api<Config | null>("/admin/exam-config").then((r) => setC(r ?? DEFAULT)).catch((e) => toast(e.message, "error"));
  }, []);
  if (!c) return <Loading />;

  const setRule = (i: number, patch: Partial<Rule>) => setC({ ...c, rules: c.rules.map((r, j) => (j === i ? { ...r, ...patch } : r)), availability: undefined });
  const setGrade = (i: number, patch: Partial<Grade>) => setC({ ...c, grades: c.grades.map((g, j) => (j === i ? { ...g, ...patch } : g)) });
  const totalQ = c.rules.reduce((s, r) => s + (Number(r.count) || 0), 0);
  const totalPts = c.rules.reduce((s, r) => s + (Number(r.count) || 0) * (Number(r.points) || 0), 0);

  async function save() {
    if (!c) return;
    setBusy(true);
    try {
      const clean = {
        ...c,
        rules: c.rules.map((r) => ({ count: Number(r.count), points: Number(r.points), difficulty: r.difficulty || null, period: r.period || null, topic: r.topic || null })),
        grades: c.grades.map((g) => ({ min_percent: Number(g.min_percent), grade: g.grade })),
      };
      setC(await api<Config>("/admin/exam-config", { method: "PUT", body: clean }));
      toast("Imtihon formati saqlandi", "success");
    } catch (e) {
      toast((e as Error).message, "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="stack">
      <h1>Imtihon formati</h1>
      <p className="muted">Rasmiy spetsifikatsiya e’lon qilinganda shu yerda o‘zgartirasiz — kodga tegish shart emas.</p>
      <div className="card grid-2" style={{ gridTemplateColumns: "2fr 1fr 1fr" }}>
        <label className="field"><span>Nomi</span><input className="input" value={c.name} onChange={(e) => setC({ ...c, name: e.target.value })} /></label>
        <label className="field"><span>Vaqt (daqiqa)</span><input className="input" type="number" value={c.duration_minutes} onChange={(e) => setC({ ...c, duration_minutes: Number(e.target.value) })} /></label>
        <label className="field"><span>Maksimal ball</span><input className="input" type="number" value={c.max_score} onChange={(e) => setC({ ...c, max_score: Number(e.target.value) })} /></label>
      </div>

      <div className="card stack">
        <div className="row between">
          <div><div className="bold">Savollar qoidalari</div><div className="small muted">Har qoida bo‘yicha bazadan tasodifiy savollar olinadi. Filtrlar ixtiyoriy.</div></div>
          <button className="btn sm white" onClick={() => setC({ ...c, rules: [...c.rules, { count: 5, points: 1 }] })}><Plus size={18} /> Qoida</button>
        </div>
        <div className="rule-row tiny muted bold"><span className="rule-head">Soni</span><span className="rule-head">Ball</span><span className="rule-head">Qiyinlik</span><span className="rule-head">Davr</span><span className="rule-head">Mavzu</span><span /></div>
        {c.rules.map((r, i) => {
          const topics = periods.find((p) => p.name === r.period)?.topics ?? periods.flatMap((p) => p.topics);
          const avail = c.availability?.[i];
          return (
            <div key={i}>
              <div className="rule-row">
                <input className="input" type="number" min={1} value={r.count} onChange={(e) => setRule(i, { count: Number(e.target.value) })} title="Savollar soni" />
                <input className="input" type="number" step="0.5" min={0.5} value={r.points} onChange={(e) => setRule(i, { points: Number(e.target.value) })} title="Har savol bali" />
                <select className="select" value={r.difficulty ?? ""} onChange={(e) => setRule(i, { difficulty: e.target.value ? Number(e.target.value) : null })}>
                  <option value="">Har qanday</option>
                  {[1, 2, 3].map((d) => <option key={d} value={d}>{DIFFICULTY[d]}</option>)}
                </select>
                <select className="select" value={r.period ?? ""} onChange={(e) => setRule(i, { period: e.target.value || null, topic: null })}>
                  <option value="">Barcha davrlar</option>
                  {periods.map((p) => <option key={p.id} value={p.name}>{p.name}</option>)}
                </select>
                <select className="select" value={r.topic ?? ""} onChange={(e) => setRule(i, { topic: e.target.value || null })}>
                  <option value="">Barcha mavzular</option>
                  {topics.map((t) => <option key={t.id} value={t.name}>{t.name}</option>)}
                </select>
                <button className="icon-btn" disabled={c.rules.length === 1} onClick={() => setC({ ...c, rules: c.rules.filter((_, j) => j !== i) })}><Trash size={18} /></button>
              </div>
              {avail !== undefined && avail < r.count && (
                <div className="tiny" style={{ color: "var(--danger)", fontWeight: 600, marginTop: 4 }}>Bazada faqat {avail} ta mos savol bor (kerak: {r.count})</div>
              )}
            </div>
          );
        })}
        <div className="small bold">Jami: {totalQ} ta savol · {totalPts} xom ball → {c.max_score} ballik shkalaga keltiriladi</div>
      </div>

      <div className="card stack">
        <div className="row between">
          <div><div className="bold">Darajalar</div><div className="small muted">Foiz chegarasi bo‘yicha (yuqoridan pastga)</div></div>
          <button className="btn sm white" onClick={() => setC({ ...c, grades: [...c.grades, { min_percent: 0, grade: "" }] })}><Plus size={18} /> Daraja</button>
        </div>
        {c.grades.map((g, i) => (
          <div key={i} className="row">
            <input className="input" style={{ width: 100 }} value={g.grade} placeholder="A+" onChange={(e) => setGrade(i, { grade: e.target.value })} />
            <input className="input" style={{ width: 100 }} type="number" value={g.min_percent} onChange={(e) => setGrade(i, { min_percent: Number(e.target.value) })} />
            <span className="small muted grow">% va undan yuqori</span>
            <button className="icon-btn" disabled={c.grades.length === 1} onClick={() => setC({ ...c, grades: c.grades.filter((_, j) => j !== i) })}><Trash size={18} /></button>
          </div>
        ))}
      </div>
      <button className="btn block" disabled={busy || !c.name.trim() || c.grades.some((g) => !g.grade.trim())} onClick={save}>Saqlash</button>
    </div>
  );
}
