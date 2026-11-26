import { useRef, useState } from "react";
import { Trash } from "../../components/Icons";
import { Segmented, Sheet, Switch, toast } from "../../components/ui";
import { api } from "../../lib/api";
import { confirmDialog } from "../../lib/telegram";
import { DIFFICULTY, type AdminPeriod, type AdminQuestion } from "./shared";

type Draft = Omit<AdminQuestion, "id" | "period" | "topic">;
const EMPTY: Draft = { text: "", a: "", b: "", c: "", d: "", correct: "a", explanation: "", difficulty: 1, period_id: null, topic_id: null, is_active: true, image_url: null };

/** Savol qo‘shish / tahrirlash oynasi */
export function QuestionForm({ question, periods, onClose, onSaved }: {
  question: AdminQuestion | null; periods: AdminPeriod[]; onClose: () => void; onSaved: () => void;
}) {
  const [d, setD] = useState<Draft>(question ? { ...question } : { ...EMPTY, period_id: periods[0]?.id ?? null });
  const [busy, setBusy] = useState(false);
  const set = <K extends keyof Draft>(k: K, v: Draft[K]) => setD((x) => ({ ...x, [k]: v }));
  const topics = periods.find((p) => p.id === d.period_id)?.topics ?? [];
  const valid = d.text.trim() && d.a.trim() && d.b.trim() && d.c.trim() && d.d.trim();

  async function save() {
    setBusy(true);
    try {
      await api(question ? `/admin/questions/${question.id}` : "/admin/questions", {
        method: question ? "PUT" : "POST", body: d,
      });
      toast(question ? "Saqlandi" : "Savol qo‘shildi", "success");
      onSaved();
    } catch (e) {
      toast((e as Error).message, "error");
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    if (!question || !(await confirmDialog("Savolni o‘chirasizmi?"))) return;
    try {
      const r = await api<{ deleted: boolean }>(`/admin/questions/${question.id}`, { method: "DELETE" });
      toast(r.deleted ? "Savol o‘chirildi" : "Savolga javoblar bor — u o‘chirib qo‘yildi (statistika saqlanadi)", "success");
      onSaved();
    } catch (e) {
      toast((e as Error).message, "error");
    }
  }

  return (
    <Sheet onClose={onClose}>
      <div className="stack">
        <div className="row between">
          <h2 style={{ fontSize: 22 }}>{question ? `Savol #${question.id}` : "Yangi savol"}</h2>
          <div className="row small bold">Faol <Switch on={d.is_active} onChange={(v) => set("is_active", v)} /></div>
        </div>
        <label className="field"><span>Savol matni</span>
          <textarea className="textarea" value={d.text} onChange={(e) => set("text", e.target.value)} />
        </label>
        <ImageField value={d.image_url} onChange={(v) => set("image_url", v)} />
        <div className="field"><span>Variantlar (to‘g‘ri javobni harf ustiga bosib belgilang)</span>
          {(["a", "b", "c", "d"] as const).map((k) => (
            <div key={k} className="opt-edit">
              <button type="button" className={`radio ${d.correct === k ? "on" : ""}`} onClick={() => set("correct", k)}>{k.toUpperCase()}</button>
              <input className="input" value={d[k]} onChange={(e) => set(k, e.target.value)} placeholder={`${k.toUpperCase()} variant`} />
            </div>
          ))}
        </div>
        <label className="field"><span>Izoh (javobdan keyin ko‘rsatiladi)</span>
          <textarea className="textarea" value={d.explanation} onChange={(e) => set("explanation", e.target.value)} />
        </label>
        <div className="grid-2">
          <label className="field"><span>Davr</span>
            <select className="select" value={d.period_id ?? ""} onChange={(e) => setD((x) => ({ ...x, period_id: e.target.value ? Number(e.target.value) : null, topic_id: null }))}>
              <option value="">— tanlanmagan —</option>
              {periods.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </label>
          <label className="field"><span>Mavzu</span>
            <select className="select" value={d.topic_id ?? ""} onChange={(e) => set("topic_id", e.target.value ? Number(e.target.value) : null)}>
              <option value="">— tanlanmagan —</option>
              {topics.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </label>
        </div>
        <div className="field"><span>Qiyinlik</span>
          <Segmented<number> value={d.difficulty} onChange={(v) => set("difficulty", v)}
            options={[1, 2, 3].map((n) => ({ value: n, label: DIFFICULTY[n] }))} />
        </div>
        <div className="row">
          {question && <button className="btn red" onClick={remove} aria-label="O‘chirish"><Trash size={20} /></button>}
          <button className="btn white grow" onClick={onClose}>Bekor qilish</button>
          <button className="btn grow" disabled={!valid || busy} onClick={save}>Saqlash</button>
        </div>
      </div>
    </Sheet>
  );
}

/** Rasm: fayl yuklash yoki havola kiritish */
function ImageField({ value, onChange }: { value: string | null; onChange: (v: string | null) => void }) {
  const input = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);

  async function upload(file: File) {
    const form = new FormData();
    form.append("file", file);
    setBusy(true);
    try {
      const r = await api<{ url: string }>("/admin/media", { form });
      onChange(r.url);
    } catch (e) {
      toast((e as Error).message, "error");
    } finally {
      setBusy(false);
      if (input.current) input.current.value = "";
    }
  }

  return (
    <div className="field"><span>Rasm (ixtiyoriy — xarita, portret, hujjat...)</span>
      <div className="image-field">
        <div className="thumb">{value ? <img src={value} alt="" /> : "Rasm yo‘q"}</div>
        <div className="stack grow" style={{ gap: 8, minWidth: 200 }}>
          <div className="row">
            <button type="button" className="btn sm white" disabled={busy} onClick={() => input.current?.click()}>
              {busy ? "Yuklanmoqda..." : "Rasm yuklash"}
            </button>
            {value && <button type="button" className="btn sm red" onClick={() => onChange(null)}>Olib tashlash</button>}
          </div>
          <input className="input" placeholder="yoki https://... havola" value={value ?? ""}
            onChange={(e) => onChange(e.target.value || null)} />
          <div className="tiny muted">PNG, JPG, WEBP yoki GIF · 2 MB gacha</div>
        </div>
        <input ref={input} type="file" accept="image/png,image/jpeg,image/webp,image/gif" hidden
          onChange={(e) => { const f = e.target.files?.[0]; if (f) void upload(f); }} />
      </div>
    </div>
  );
}
