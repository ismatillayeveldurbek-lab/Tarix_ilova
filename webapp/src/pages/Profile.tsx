import { useState } from "react";
import { Bell, ChevronRight, Shield } from "../components/Icons";
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
      <div className="center stack" style={{ alignItems: "center", gap: 6, paddingTop: 8 }}>
        <Avatar name={u.name || "?"} size="xl" />
        <h1 style={{ fontSize: 24 }}>{u.name}</h1>
        {u.is_admin && <span className="chip purple">Admin</span>}
      </div>

      <div className="section-title">Statistika</div>
      <div className="grid-2" style={{ gridTemplateColumns: "1fr 1fr" }}>
        <div className="stat-card" style={{ "--c": "var(--orange)" } as React.CSSProperties}><div className="v">🔥 {u.streak}</div><div className="l">Ketma-ket kunlar</div></div>
        <div className="stat-card" style={{ "--c": "var(--gold)" } as React.CSSProperties}><div className="v">🏆 {u.streak_best}</div><div className="l">Rekord</div></div>
        <div className="stat-card" style={{ "--c": "var(--blue)" } as React.CSSProperties}><div className="v">{home.totals.answers}</div><div className="l">Jami javoblar</div></div>
        <div className="stat-card" style={{ "--c": "var(--green)" } as React.CSSProperties}><div className="v">{accuracy}%</div><div className="l">Aniqlik</div></div>
      </div>

      <button className="card tap row" onClick={() => navigate("/progress")}>
        <Ring value={home.mastery / 100} size={64} stroke={7} color={levelColor(home.mastery)}>
          <span className="bold">{home.mastery}%</span>
        </Ring>
        <div className="grow"><div className="bold">O'zlashtirish</div><div className="small muted">Mavzular bo'yicha natijalar va zaif mavzular</div></div>
        <ChevronRight />
      </button>

      <button className="card tap row" onClick={() => navigate("/invite")}>
        <span className="rec-icon" style={{ background: "var(--blue-soft)" }}>👥</span>
        <div className="grow"><div className="bold">Do'stlarni taklif qilish</div><div className="small muted">Har bir faol do'st uchun XP bonus</div></div>
        <ChevronRight />
      </button>

      <div className="card"><div className="bold" style={{ marginBottom: 10 }}>Shu hafta</div><WeekStrip /></div>

      <div className="section-title">Sozlamalar</div>
      <div className="card" style={{ paddingTop: 4, paddingBottom: 4 }}>
        <div className="setting-row">
          <Bell /><div className="grow"><div className="bold">Kunlik eslatma</div><div className="small muted">{`Kuniga ${home.today.goal} ta savol`}</div></div>
          <Switch on={u.reminder_enabled} onChange={(v) => update({ reminder_enabled: v })} />
        </div>
        {u.reminder_enabled && (
          <div className="setting-row">
            <span style={{ width: 24 }} /><div className="grow bold">Eslatma vaqti</div>
            <input type="time" className="input" style={{ width: 120 }} value={u.reminder_time} disabled={saving}
              onChange={(e) => e.target.value && update({ reminder_time: e.target.value })} />
          </div>
        )}
      </div>

      {u.is_admin && (
        <button className="card tap row" onClick={() => navigate("/admin")}>
          <span style={{ color: "var(--purple)" }}><Shield /></span>
          <div className="grow"><div className="bold">Admin panel</div><div className="small muted">Savollar, import, imtihon formati</div></div>
          <ChevronRight />
        </button>
      )}
    </div>
  );
}
