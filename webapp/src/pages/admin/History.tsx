import { useCallback, useEffect, useState } from "react";
import { Edit, Plus, Trash } from "../../components/Icons";
import { Sheet, toast } from "../../components/ui";
import { api, download } from "../../lib/api";
import { navigate } from "../../lib/router";
import { confirmDialog } from "../../lib/telegram";

type Event = { id: number; month: number; day: number; year: number | null; title: string; text: string };
const MONTHS = ["Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun", "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr"];

export function HistoryPage() {
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [events, setEvents] = useState<Event[]>([]);
  const [editing, setEditing] = useState<Partial<Event> | null>(null);

  const load = useCallback(() => api<Event[]>(`/admin/history?month=${month}`).then(setEvents).catch((e) => toast(e.message, "error")), [month]);
  useEffect(() => { void load(); }, [load]);

  async function save() {
    if (!editing) return;
    try {
      const body = { ...editing, year: editing.year || null, text: editing.text || "" };
      await api(editing.id ? `/admin/history/${editing.id}` : "/admin/history", { method: editing.id ? "PUT" : "POST", body });
      toast("Saqlandi", "success");
      setEditing(null);
      if (editing.month && editing.month !== month) setMonth(editing.month); else void load();
    } catch (e) {
      toast((e as Error).message, "error");
    }
  }

  async function remove(e: Event) {
    if (!(await confirmDialog(`"${e.title}" o'chirilsinmi?`))) return;
    await api(`/admin/history/${e.id}`, { method: "DELETE" }).catch((err) => toast(err.message, "error"));
    void load();
  }

  const today = new Date();
  return (
    <div className="stack">
      <div className="row between">
        <h1>Tarixda bugun</h1>
        <div className="row">
          <button className="btn sm white" onClick={() => navigate("/admin/import")}>Import</button>
          <button className="btn sm white" onClick={() => download("/admin/export/history.xlsx", "voqealar.xlsx").catch((e) => toast(e.message, "error"))}>Excel</button>
          <button className="btn sm" onClick={() => setEditing({ month, day: 1 })}><Plus size={18} /> Voqea</button>
        </div>
      </div>
      <p className="muted">Har kuni belgilangan vaqtda (standart 09:00) shu kunga oid voqealar kanalga va bot foydalanuvchilariga avtomatik yuboriladi.</p>
      <div className="row" style={{ flexWrap: "wrap", gap: 6 }}>
        {MONTHS.map((m, i) => (
          <button key={m} className={`btn sm ${month === i + 1 ? "blue" : "white"}`} onClick={() => setMonth(i + 1)}>{m}</button>
        ))}
      </div>
      <div className="stack" style={{ gap: 8 }}>
        {events.length === 0 && <div className="card muted center">Bu oy uchun voqea yo'q</div>}
        {events.map((e) => {
          const isToday = e.month === today.getMonth() + 1 && e.day === today.getDate();
          return (
            <div key={e.id} className="card row" style={isToday ? { borderColor: "var(--primary-text)" } : undefined}>
              <div className="center" style={{ minWidth: 54 }}>
                <div style={{ fontSize: 24, fontWeight: 600, color: "var(--primary-text)" }}>{e.day}</div>
                <div className="tiny muted bold">{MONTHS[e.month - 1].slice(0, 3)}</div>
              </div>
              <div className="grow">
                <div className="bold">{e.year ? `${e.year} · ` : ""}{e.title} {isToday && <span className="chip blue">bugun</span>}</div>
                <div className="small muted">{e.text}</div>
              </div>
              <button className="icon-btn" onClick={() => setEditing(e)}><Edit size={18} /></button>
              <button className="icon-btn" onClick={() => remove(e)}><Trash size={18} /></button>
            </div>
          );
        })}
      </div>
      {editing && (
        <Sheet onClose={() => setEditing(null)}>
          <div className="stack">
            <h2 style={{ fontSize: 20 }}>{editing.id ? "Voqeani tahrirlash" : "Yangi voqea"}</h2>
            <div className="grid-2" style={{ gridTemplateColumns: "1fr 1fr 1fr" }}>
              <label className="field"><span>Oy</span>
                <select className="select" value={editing.month} onChange={(e) => setEditing({ ...editing, month: Number(e.target.value) })}>
                  {MONTHS.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
                </select>
              </label>
              <label className="field"><span>Kun</span>
                <input className="input" type="number" min={1} max={31} value={editing.day ?? ""} onChange={(e) => setEditing({ ...editing, day: Number(e.target.value) })} />
              </label>
              <label className="field"><span>Yil</span>
                <input className="input" type="number" value={editing.year ?? ""} onChange={(e) => setEditing({ ...editing, year: e.target.value ? Number(e.target.value) : null })} />
              </label>
            </div>
            <label className="field"><span>Sarlavha</span>
              <input className="input" value={editing.title ?? ""} onChange={(e) => setEditing({ ...editing, title: e.target.value })} />
            </label>
            <label className="field"><span>Matn</span>
              <textarea className="textarea" value={editing.text ?? ""} onChange={(e) => setEditing({ ...editing, text: e.target.value })} />
            </label>
            <div className="row">
              <button className="btn white grow" onClick={() => setEditing(null)}>Bekor qilish</button>
              <button className="btn grow" disabled={!editing.title?.trim() || !editing.day} onClick={save}>Saqlash</button>
            </div>
          </div>
        </Sheet>
      )}
    </div>
  );
}
