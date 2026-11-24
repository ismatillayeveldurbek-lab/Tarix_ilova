import { useState } from "react";
import { Bell, ChevronRight, Globe, Shield } from "../components/Icons";
import { WeekStrip } from "../components/WeekStrip";
import { Avatar, Segmented, Switch, toast } from "../components/ui";
import { api } from "../lib/api";
import { navigate } from "../lib/router";
import { useStore } from "../lib/store";
import type { Alphabet } from "../lib/translit";

export function ProfilePage() {
  const { home, t, reload, setHome } = useStore();
  const [saving, setSaving] = useState(false);
  if (!home) return null;
  const u = home.user;
  const accuracy = home.totals.answers ? Math.round((home.totals.correct / home.totals.answers) * 100) : 0;

  async function update(patch: Partial<{ alphabet: Alphabet; reminder_enabled: boolean; reminder_time: string }>) {
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

      <div className="section-title">{t("Statistika")}</div>
      <div className="grid-2" style={{ gridTemplateColumns: "1fr 1fr" }}>
        <div className="stat-card" style={{ "--c": "var(--orange)" } as React.CSSProperties}><div className="v">🔥 {u.streak}</div><div className="l">{t("Ketma-ket kunlar")}</div></div>
        <div className="stat-card" style={{ "--c": "var(--gold)" } as React.CSSProperties}><div className="v">🏆 {u.streak_best}</div><div className="l">{t("Rekord")}</div></div>
        <div className="stat-card" style={{ "--c": "var(--blue)" } as React.CSSProperties}><div className="v">{home.totals.answers}</div><div className="l">{t("Jami javoblar")}</div></div>
        <div className="stat-card" style={{ "--c": "var(--green)" } as React.CSSProperties}><div className="v">{accuracy}%</div><div className="l">{t("Aniqlik")}</div></div>
      </div>

      <div className="card"><div className="bold" style={{ marginBottom: 10 }}>{t("Shu hafta")}</div><WeekStrip /></div>

      <div className="section-title">{t("Sozlamalar")}</div>
      <div className="card" style={{ paddingTop: 4, paddingBottom: 4 }}>
        <div className="setting-row">
          <Globe /><div className="grow bold">{t("Alifbo")}</div>
          <div style={{ width: 170 }}>
            <Segmented<Alphabet> value={u.alphabet} onChange={(v) => update({ alphabet: v })}
              options={[{ value: "latn", label: "Lotin" }, { value: "cyrl", label: "Кирилл" }]} />
          </div>
        </div>
        <div className="setting-row">
          <Bell /><div className="grow"><div className="bold">{t("Kunlik eslatma")}</div><div className="small muted">{t(`Kuniga ${home.today.goal} ta savol`)}</div></div>
          <Switch on={u.reminder_enabled} onChange={(v) => update({ reminder_enabled: v })} />
        </div>
        {u.reminder_enabled && (
          <div className="setting-row">
            <span style={{ width: 24 }} /><div className="grow bold">{t("Eslatma vaqti")}</div>
            <input type="time" className="input" style={{ width: 120 }} value={u.reminder_time} disabled={saving}
              onChange={(e) => e.target.value && update({ reminder_time: e.target.value })} />
          </div>
        )}
      </div>

      {u.is_admin && (
        <button className="card tap row" onClick={() => navigate("/admin")}>
          <span style={{ color: "var(--purple)" }}><Shield /></span>
          <div className="grow"><div className="bold">{t("Admin panel")}</div><div className="small muted">{t("Savollar, import, imtihon formati")}</div></div>
          <ChevronRight />
        </button>
      )}
    </div>
  );
}
