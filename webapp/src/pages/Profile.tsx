import { useState } from "react";
import { Bell, ChevronRight, Flame, Shield, Users } from "../components/Icons";
import { WeekStrip } from "../components/WeekStrip";
import { Avatar, levelColor, Ring, Switch, toast } from "../components/ui";
import { api } from "../lib/api";
import { navigate } from "../lib/router";
import { useStore } from "../lib/store";

export function ProfilePage() {
  const { home, reload, setHome } = useStore();
  const [saving, setSaving] = useState(false);
  if (!home) return null;
  const u = home.user;
  const accuracy = home.totals.answers ? Math.round((home.totals.correct / home.totals.answers) * 100) : 0;

  async function update(patch: Partial<{ reminder_enabled: boolean; reminder_time: string }>) {
    if (!home) return;
    setHome({ ...home, user: { ...home.user, ...patch } }); // darhol ko'rsatamiz
    setSaving(true);
    try {
      await api("/me", { method: "PATCH", body: patch });
      await reload();
    } catch (e) {
      toast((e as Error).message, "error");
      await reload();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="page stack">
      <div className="row" style={{ gap: 14, paddingTop: 4 }}>
        <Avatar name={u.name || "?"} size="xl" />
        <div className="grow">
          <h1 style={{ fontSize: 23 }}>{u.name}</h1>
          <div className="row" style={{ gap: 6, marginTop: 4 }}>
            {u.is_admin && <span className="chip blue">Admin</span>}
            <span className="chip">{home.user.streak_best} kunlik rekord</span>
          </div>
        </div>
      </div>

      <div className="metrics">
        <div className="metric"><span className="label"><Flame size={14} /> Ketma-ket</span><span className="value">{u.streak}<small>kun</small></span></div>
        <div className="metric"><span className="label">Javoblar</span><span className="value">{home.totals.answers}</span></div>
        <div className="metric"><span className="label">Aniqlik</span><span className="value">{accuracy}<small>%</small></span></div>
      </div>

      <button className="card tap row" onClick={() => navigate("/progress")}>
        <Ring value={home.mastery / 100} size={56} stroke={5} color={levelColor(home.mastery)}>
          <span className="small bold num">{home.mastery}%</span>
        </Ring>
        <div className="grow"><div className="bold">O'zlashtirish</div><div className="small muted">Mavzular bo'yicha natijalar va zaif mavzular</div></div>
        <ChevronRight size={18} />
      </button>

      <div className="card"><div className="eyebrow" style={{ marginBottom: 12 }}>Shu hafta</div><WeekStrip /></div>

      <button className="card tap row" onClick={() => navigate("/invite")}>
        <span className="icon-box"><Users size={20} /></span>
        <div className="grow"><div className="bold">Do'stlarni taklif qilish</div><div className="small muted">Har bir faol do'st uchun bonus XP</div></div>
        <ChevronRight size={18} />
      </button>

      <div className="section-title"><span>Sozlamalar</span></div>
      <div className="card" style={{ paddingTop: 4, paddingBottom: 4 }}>
        <div className="setting-row">
          <span className="icon-box"><Bell size={20} /></span><div className="grow"><div className="bold">Kunlik eslatma</div><div className="small muted">{`Kuniga ${home.today.goal} ta savol`}</div></div>
          <Switch on={u.reminder_enabled} onChange={(v) => update({ reminder_enabled: v })} />
        </div>
        {u.reminder_enabled && (
          <div className="setting-row">
            <span style={{ width: 40 }} /><div className="grow bold">Eslatma vaqti</div>
            <input type="time" className="input" style={{ width: 120 }} value={u.reminder_time} disabled={saving}
              onChange={(e) => e.target.value && update({ reminder_time: e.target.value })} />
          </div>
        )}
      </div>

      {u.is_admin && (
        <button className="card tap row" onClick={() => navigate("/admin")}>
          <span className="icon-box"><Shield size={20} /></span>
          <div className="grow"><div className="bold">Admin panel</div><div className="small muted">Savollar, import, imtihon formati</div></div>
          <ChevronRight size={18} />
        </button>
      )}
    </div>
  );
}
