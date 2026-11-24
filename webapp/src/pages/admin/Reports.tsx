import { useCallback, useEffect, useState } from "react";
import { Segmented, toast } from "../../components/ui";
import { api } from "../../lib/api";
import { QuestionForm } from "./QuestionForm";
import { usePeriods, type AdminQuestion } from "./shared";

type Report = { id: number; comment: string; status: string; created_at: string; user: string; question: AdminQuestion };

export function ReportsPage({ onCount }: { onCount: (n: number) => void }) {
  const { periods } = usePeriods();
  const [status, setStatus] = useState("new");
  const [rows, setRows] = useState<Report[]>([]);
  const [editing, setEditing] = useState<AdminQuestion | null>(null);

  const load = useCallback(async () => {
    try {
      const r = await api<Report[]>(`/admin/reports?status=${status}`);
      setRows(r);
      if (status === "new") onCount(r.length);
    } catch (e) {
      toast((e as Error).message, "error");
    }
  }, [status, onCount]);
  useEffect(() => { void load(); }, [load]);

  async function resolve(r: Report, newStatus: string, deactivate = false) {
    try {
      await api(`/admin/reports/${r.id}`, { body: { status: newStatus, deactivate } });
      toast("Belgilandi", "success");
      void load();
    } catch (e) {
      toast((e as Error).message, "error");
    }
  }

  return (
    <div className="stack">
      <h1>Xato xabarlari</h1>
      <div style={{ maxWidth: 420 }}>
        <Segmented value={status} onChange={setStatus}
          options={[{ value: "new", label: "Yangi" }, { value: "fixed", label: "Tuzatilgan" }, { value: "rejected", label: "Rad etilgan" }]} />
      </div>
      {rows.length === 0 && <div className="card muted center">Xabar yo'q 🎉</div>}
      {rows.map((r) => {
        const q = r.question;
        return (
          <div key={r.id} className="card stack" style={{ gap: 8 }}>
            <div className="row between small muted">
              <span>#{r.id} · {r.user} · {new Date(r.created_at).toLocaleString()}</span>
              <span>Savol #{q.id}{!q.is_active && " (o'chirilgan)"}</span>
            </div>
            <div className="card" style={{ background: "var(--red-soft)", border: 0, boxShadow: "none", padding: 12 }}>💬 {r.comment}</div>
            <div className="bold">{q.text}</div>
            <div className="small">
              {(["a", "b", "c", "d"] as const).map((k) => (
                <div key={k} style={k === q.correct ? { color: "var(--green-dark)", fontWeight: 800 } : undefined}>
                  {k.toUpperCase()}) {q[k]} {k === q.correct && "✓"}
                </div>
              ))}
            </div>
            {q.explanation && <div className="small muted">💡 {q.explanation}</div>}
            <div className="row" style={{ flexWrap: "wrap" }}>
              <button className="btn sm blue" onClick={() => setEditing(q)}>Savolni tahrirlash</button>
              {status !== "fixed" && <button className="btn sm" onClick={() => resolve(r, "fixed")}>✓ Tuzatildi</button>}
              {status !== "rejected" && <button className="btn sm white" onClick={() => resolve(r, "rejected")}>Rad etish</button>}
              {q.is_active && <button className="btn sm red" onClick={() => resolve(r, "fixed", true)}>Savolni o'chirish</button>}
            </div>
          </div>
        );
      })}
      {editing && <QuestionForm question={editing} periods={periods} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); void load(); }} />}
    </div>
  );
}
