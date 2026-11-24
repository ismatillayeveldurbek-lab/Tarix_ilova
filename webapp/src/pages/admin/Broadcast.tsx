import { useCallback, useEffect, useState } from "react";
import { Progress, Segmented, toast } from "../../components/ui";
import { api } from "../../lib/api";
import { confirmDialog } from "../../lib/telegram";

type Status = { total?: number; sent?: number; failed?: number; running?: boolean; started_at?: string };
type Info = { status: Status; recipients: number; bot_ready: boolean };
type Audience = "all" | "active7" | "active30";

export function BroadcastPage() {
  const [text, setText] = useState("");
  const [audience, setAudience] = useState<Audience>("all");
  const [info, setInfo] = useState<Info | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => api<Info>(`/admin/broadcast?audience=${audience}`).then(setInfo).catch((e) => toast(e.message, "error")), [audience]);
  useEffect(() => { void load(); }, [load]);
  // Yuborilayotganda progressni har 2 soniyada yangilaymiz
  useEffect(() => {
    if (!info?.status.running) return;
    const id = setInterval(load, 2000);
    return () => clearInterval(id);
  }, [info?.status.running, load]);

  async function send() {
    if (!info || !(await confirmDialog(`E'lon ${info.recipients} ta foydalanuvchiga yuborilsinmi?`))) return;
    setBusy(true);
    try {
      const r = await api<{ queued: number }>("/admin/broadcast", { body: { text, audience } });
      toast(`${r.queued} ta foydalanuvchiga yuborilmoqda`, "success");
      setText("");
      void load();
    } catch (e) {
      toast((e as Error).message, "error");
    } finally {
      setBusy(false);
    }
  }

  const s = info?.status ?? {};
  return (
    <div className="stack">
      <h1>E'lon yuborish</h1>
      <p className="muted">Xabar bot orqali barcha tanlangan foydalanuvchilarga yuboriladi.</p>
      {info && !info.bot_ready && (
        <div className="card" style={{ borderColor: "var(--red)", background: "var(--red-soft)" }}>
          Bot ishga tushmagan. Ilovani <code>python -m app.main</code> orqali ishga tushiring.
        </div>
      )}
      <div className="grid-2">
        <div className="card stack">
          <div className="field"><span>Kimga</span>
            <Segmented<Audience> value={audience} onChange={setAudience} options={[
              { value: "all", label: "Hammaga" }, { value: "active7", label: "7 kunda faol" }, { value: "active30", label: "30 kunda faol" },
            ]} />
          </div>
          <label className="field"><span>Matn</span>
            <textarea className="textarea" style={{ minHeight: 160 }} maxLength={4000} value={text}
              placeholder="Masalan: Yangi 50 ta savol qo'shildi! Temuriylar davri bo'yicha mashq qiling 💪"
              onChange={(e) => setText(e.target.value)} />
          </label>
          <div className="row between small muted">
            <span>{info ? `${info.recipients} ta qabul qiluvchi` : "..."}</span><span>{text.length}/4000</span>
          </div>
          <button className="btn block" disabled={!text.trim() || busy || !info?.bot_ready || !!s.running} onClick={send}>Yuborish</button>
        </div>
        <div className="stack">
          {s.total !== undefined && (
            <div className="card stack" style={{ gap: 8 }}>
              <div className="bold">{s.running ? "Yuborilmoqda..." : "Oxirgi e'lon"}</div>
              <Progress value={s.total ? ((s.sent ?? 0) + (s.failed ?? 0)) / s.total : 1} />
              <div className="row small" style={{ flexWrap: "wrap" }}>
                <span className="chip green">✅ Yuborildi: {s.sent}</span>
                <span className="chip red">❌ Yetmadi: {s.failed}</span>
                <span className="chip">Jami: {s.total}</span>
              </div>
              <div className="tiny muted">Botni bloklagan foydalanuvchilar avtomatik belgilanadi va keyingi e'lonlarda hisobga olinmaydi.</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
