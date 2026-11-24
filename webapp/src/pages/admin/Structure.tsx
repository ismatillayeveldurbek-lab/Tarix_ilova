import { useState } from "react";
import { Check, Edit, Plus, Trash } from "../../components/Icons";
import { toast } from "../../components/ui";
import { api } from "../../lib/api";
import { confirmDialog } from "../../lib/telegram";
import { usePeriods } from "./shared";

/** Nomni joyida tahrirlash maydoni */
function InlineName({ value, order, onSave, onDelete, count }: {
  value: string; order: number; count: number;
  onSave: (name: string, order: number) => Promise<void>; onDelete: () => Promise<void>;
}) {
  const [edit, setEdit] = useState(false);
  const [name, setName] = useState(value);
  const [ord, setOrd] = useState(order);
  if (!edit) {
    return (
      <div className="row grow">
        <span className="grow bold">{value}</span>
        <span className="chip">{count} savol</span>
        <button className="icon-btn" onClick={() => setEdit(true)} aria-label="Tahrirlash"><Edit size={18} /></button>
        <button className="icon-btn" onClick={onDelete} aria-label="O'chirish"><Trash size={18} /></button>
      </div>
    );
  }
  return (
    <div className="row grow">
      <input className="input" style={{ width: 64, padding: "8px" }} type="number" value={ord} onChange={(e) => setOrd(Number(e.target.value))} title="Tartib raqami" />
      <input className="input grow" style={{ padding: "8px 12px" }} value={name} onChange={(e) => setName(e.target.value)} autoFocus />
      <button className="btn sm" onClick={async () => { await onSave(name, ord); setEdit(false); }}><Check size={18} /></button>
    </div>
  );
}

export function StructurePage() {
  const { periods, reload } = usePeriods();
  const [newPeriod, setNewPeriod] = useState("");
  const [newTopic, setNewTopic] = useState<Record<number, string>>({});

  const run = async (fn: () => Promise<unknown>, ok?: string) => {
    try {
      await fn();
      if (ok) toast(ok, "success");
      await reload();
    } catch (e) {
      toast((e as Error).message, "error");
    }
  };
  const confirmDel = async (what: string, fn: () => Promise<unknown>) => {
    if (await confirmDialog(`${what} o'chirilsinmi?`)) await run(fn, "O'chirildi");
  };

  return (
    <div className="stack">
      <h1>Davr va mavzular</h1>
      <p className="muted">Mini App'dagi "mavzular yo'li" shu tartibda ko'rinadi. Tartib raqami kichik bo'lgani yuqorida turadi.</p>
      <div className="card row">
        <input className="input grow" placeholder="Yangi davr nomi (masalan: Qadimgi davr)" value={newPeriod} onChange={(e) => setNewPeriod(e.target.value)} />
        <button className="btn sm" disabled={!newPeriod.trim()} onClick={() => run(async () => {
          await api("/admin/periods", { body: { name: newPeriod, sort_order: periods.length + 1 } });
          setNewPeriod("");
        }, "Davr qo'shildi")}><Plus size={18} /> Davr</button>
      </div>
      {periods.map((p) => (
        <div key={p.id} className="card stack">
          <div className="row" style={{ fontSize: 18 }}>
            <span className="chip purple">{p.sort_order}</span>
            <InlineName value={p.name} order={p.sort_order} count={p.questions}
              onSave={(name, order) => run(() => api(`/admin/periods/${p.id}`, { method: "PUT", body: { name, sort_order: order } }), "Saqlandi")}
              onDelete={() => confirmDel(`"${p.name}" davri`, () => api(`/admin/periods/${p.id}`, { method: "DELETE" }))} />
          </div>
          <div className="stack" style={{ gap: 6, paddingLeft: 12, borderLeft: "3px solid var(--border)" }}>
            {p.topics.map((t) => (
              <div key={t.id} className="row">
                <span className="chip">{t.sort_order}</span>
                <InlineName value={t.name} order={t.sort_order} count={t.questions}
                  onSave={(name, order) => run(() => api(`/admin/topics/${t.id}`, { method: "PUT", body: { name, sort_order: order, period_id: p.id } }), "Saqlandi")}
                  onDelete={() => confirmDel(`"${t.name}" mavzusi`, () => api(`/admin/topics/${t.id}`, { method: "DELETE" }))} />
              </div>
            ))}
            <div className="row">
              <input className="input grow" style={{ padding: "8px 12px" }} placeholder="Yangi mavzu" value={newTopic[p.id] || ""}
                onChange={(e) => setNewTopic({ ...newTopic, [p.id]: e.target.value })} />
              <button className="btn sm white" disabled={!newTopic[p.id]?.trim()} onClick={() => run(async () => {
                await api("/admin/topics", { body: { name: newTopic[p.id], period_id: p.id, sort_order: p.topics.length + 1 } });
                setNewTopic({ ...newTopic, [p.id]: "" });
              }, "Mavzu qo'shildi")}><Plus size={18} /></button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
