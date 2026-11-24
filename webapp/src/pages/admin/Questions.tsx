import { useCallback, useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, Download, Plus } from "../../components/Icons";
import { Loading, toast } from "../../components/ui";
import { api, download } from "../../lib/api";
import { QuestionForm } from "./QuestionForm";
import { DIFFICULTY, usePeriods, type AdminQuestion } from "./shared";

type Page = { total: number; page: number; size: number; items: AdminQuestion[] };

export function QuestionsPage() {
  const { periods } = usePeriods();
  const [data, setData] = useState<Page | null>(null);
  const [q, setQ] = useState("");
  const [periodId, setPeriodId] = useState("");
  const [topicId, setTopicId] = useState("");
  const [difficulty, setDifficulty] = useState("");
  const [active, setActive] = useState("");
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState<AdminQuestion | null | "new">(null);

  const load = useCallback(async () => {
    const p = new URLSearchParams({ page: String(page), size: "20" });
    if (q) p.set("q", q);
    if (periodId) p.set("period_id", periodId);
    if (topicId) p.set("topic_id", topicId);
    if (difficulty) p.set("difficulty", difficulty);
    if (active) p.set("active", active);
    try {
      setData(await api<Page>(`/admin/questions?${p}`));
    } catch (e) {
      toast((e as Error).message, "error");
    }
  }, [q, periodId, topicId, difficulty, active, page]);

  useEffect(() => {
    const id = setTimeout(load, 250); // qidiruvda har harfda emas, biroz kutib so'raymiz
    return () => clearTimeout(id);
  }, [load]);

  const topics = periods.find((p) => String(p.id) === periodId)?.topics ?? [];
  const pages = data ? Math.max(1, Math.ceil(data.total / data.size)) : 1;
  const resetPage = <T,>(fn: (v: T) => void) => (v: T) => { fn(v); setPage(1); };

  return (
    <div className="stack">
      <div className="row between">
        <h1>Savollar {data && <span className="muted" style={{ fontSize: 18 }}>({data.total})</span>}</h1>
        <div className="row">
          <button className="btn sm white" title="Barcha savollarni Excel'ga yuklab olish (zaxira nusxa)"
            onClick={() => download("/admin/export/questions.xlsx", "savollar.xlsx").catch((e) => toast(e.message, "error"))}>
            <Download size={18} /> Excel
          </button>
          <button className="btn sm" onClick={() => setEditing("new")}><Plus size={18} /> Yangi savol</button>
        </div>
      </div>
      <div className="toolbar">
        <input className="input" placeholder="Qidirish..." value={q} onChange={(e) => resetPage(setQ)(e.target.value)} />
        <select className="select" value={periodId} onChange={(e) => { resetPage(setPeriodId)(e.target.value); setTopicId(""); }}>
          <option value="">Barcha davrlar</option>
          {periods.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
        <select className="select" value={topicId} onChange={(e) => resetPage(setTopicId)(e.target.value)} disabled={!periodId}>
          <option value="">Barcha mavzular</option>
          {topics.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>
        <select className="select" value={difficulty} onChange={(e) => resetPage(setDifficulty)(e.target.value)}>
          <option value="">Har qanday qiyinlik</option>
          {[1, 2, 3].map((d) => <option key={d} value={d}>{DIFFICULTY[d]}</option>)}
        </select>
        <select className="select" value={active} onChange={(e) => resetPage(setActive)(e.target.value)}>
          <option value="">Hammasi</option>
          <option value="true">Faol</option>
          <option value="false">O'chirilgan</option>
        </select>
      </div>
      {!data ? <Loading /> : (
        <div className="stack" style={{ gap: 8 }}>
          {data.items.length === 0 && <div className="card muted center">Hech narsa topilmadi</div>}
          {data.items.map((x) => (
            <button key={x.id} className={`q-item ${x.is_active ? "" : "inactive"}`} onClick={() => setEditing(x)}>
              <span className="q-id">#{x.id}</span>
              <div className="grow stack" style={{ gap: 4 }}>
                <div className="bold">{x.text}</div>
                <div className="small muted">✅ {x.correct.toUpperCase()}) {x[x.correct]}</div>
                <div className="row" style={{ flexWrap: "wrap", gap: 6 }}>
                  {x.period && <span className="chip blue">{x.period}</span>}
                  {x.topic && <span className="chip">{x.topic}</span>}
                  <span className="chip gold">{"★".repeat(x.difficulty)}</span>
                  {!x.is_active && <span className="chip red">o'chirilgan</span>}
                  {!x.explanation && <span className="chip red">izoh yo'q</span>}
                  {x.image_url && <span className="chip purple">🖼 rasm</span>}
                </div>
              </div>
            </button>
          ))}
          {pages > 1 && (
            <div className="row" style={{ justifyContent: "center" }}>
              <button className="btn sm white" disabled={page <= 1} onClick={() => setPage(page - 1)}><ChevronLeft size={18} /></button>
              <span className="bold">{page} / {pages}</span>
              <button className="btn sm white" disabled={page >= pages} onClick={() => setPage(page + 1)}><ChevronRight size={18} /></button>
            </div>
          )}
        </div>
      )}
      {editing && (
        <QuestionForm question={editing === "new" ? null : editing} periods={periods}
          onClose={() => setEditing(null)} onSaved={() => { setEditing(null); void load(); }} />
      )}
    </div>
  );
}
