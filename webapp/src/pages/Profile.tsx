import { useState } from "react";
import { Card, IconTile, Initials, ListRow, Pill, Screen, SectionTitle, cx } from "../components/kit";
import { Bell, Chart, Check, Flame, Shield, Trophy, Users } from "../components/Icons";
import { Switch, toast } from "../components/ui";
import { api } from "../lib/api";
import { navigate } from "../lib/router";
import { useStore } from "../lib/store";
import { haptic } from "../lib/telegram";

const DAYS = ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"];
const go = (to: string) => { haptic.tap(); navigate(to); };

export function ProfilePage() {
  const { home, reload, setHome } = useStore();
  const [saving, setSaving] = useState(false);
  if (!home) return null;
  const u = home.user;
  const accuracy = home.totals.answers ? Math.round((home.totals.correct / home.totals.answers) * 100) : 0;

  async function update(patch: Partial<{ reminder_enabled: boolean; reminder_time: string }>) {
    if (!home) return;
    setHome({ ...home, user: { ...home.user, ...patch } }); // darhol ko‘rsatamiz
    setSaving(true);
    try {
      await api("/me", { method: "PATCH", body: patch });
    } catch (e) {
      toast((e as Error).message, "error");
    } finally {
      await reload();
      setSaving(false);
    }
  }

  return (
    <Screen>
      {/* Hero */}
      <Card className="p-5">
        <div className="flex items-center gap-4">
          <Initials name={u.name || "?"} size={64} />
          <div className="min-w-0 flex-1">
            <div className="truncate text-[22px] font-extrabold tracking-tight text-ink">{u.name}</div>
            <div className="mt-1.5 flex flex-wrap gap-1.5">
              <Pill className="bg-peach-soft text-peach"><Flame size={13} /> {u.streak} kun</Pill>
              <Pill>Rekord: {u.streak_best} kun</Pill>
              {u.is_admin && <Pill className="bg-peri-soft text-peri">Admin</Pill>}
            </div>
          </div>
        </div>
        <div className="mt-5 grid grid-cols-3 divide-x divide-line rounded-2xl bg-surface-2/70 py-3 text-center">
          {[["Bu hafta", `${home.week.xp} XP`], ["Javoblar", String(home.totals.answers)], ["Aniqlik", `${accuracy}%`]].map(([l, v]) => (
            <div key={l}>
              <div className="text-[18px] font-extrabold text-ink">{v}</div>
              <div className="text-[12px] font-medium text-muted">{l}</div>
            </div>
          ))}
        </div>
      </Card>

      {/* Hafta */}
      <Card className="p-4">
        <div className="mb-3 flex items-center justify-between">
          <span className="text-[15px] font-bold text-ink">Shu hafta</span>
          <span className="text-[13px] text-muted">{home.week.days.filter((d) => d.active).length} / 7 kun faol</span>
        </div>
        <div className="flex justify-between">
          {home.week.days.map((d, i) => {
            const today = i === home.week.days.length - 1;
            return (
              <div key={d.date} className="flex flex-col items-center gap-1.5">
                <span className={cx("text-[12px] font-semibold", today ? "text-ink" : "text-faint")}>{DAYS[d.weekday]}</span>
                <span className={cx("grid h-9 w-9 place-items-center rounded-full border-2",
                  d.active ? "border-peach bg-peach text-white" : today ? "border-dashed border-peach" : "border-line")}>
                  {d.active && <Check size={16} />}
                </span>
              </div>
            );
          })}
        </div>
      </Card>

      <SectionTitle>Natijalar</SectionTitle>
      <Card className="divide-y divide-line overflow-hidden">
        <ListRow title="O‘zlashtirish" subtitle={`Mavzular bo‘yicha · ${home.mastery}%`}
          icon={<IconTile tone="success"><Chart size={20} /></IconTile>} onClick={() => go("/progress")} />
        <ListRow title="Haftalik reyting" subtitle={home.week.rank ? `${home.week.rank}-o‘rin` : "Bu hafta hali o‘rin yo‘q"}
          icon={<IconTile tone="sana"><Trophy size={20} /></IconTile>} onClick={() => go("/rating")} />
        <ListRow title="Do‘stlarni taklif qilish" subtitle="Har faol do‘st uchun bonus XP"
          icon={<IconTile tone="joy"><Users size={20} /></IconTile>} onClick={() => go("/invite")} />
      </Card>

      <SectionTitle>Sozlamalar</SectionTitle>
      <Card className="divide-y divide-line overflow-hidden">
        <div className="flex items-center gap-3 px-4 py-3.5">
          <IconTile tone="peri"><Bell size={20} /></IconTile>
          <div className="min-w-0 flex-1">
            <div className="text-[15.5px] font-semibold text-ink">Kunlik eslatma</div>
            <div className="text-[13px] text-muted">Kuniga {home.today.goal} ta savol</div>
          </div>
          <Switch on={u.reminder_enabled} onChange={(v) => update({ reminder_enabled: v })} />
        </div>
        {u.reminder_enabled && (
          <div className="flex items-center gap-3 px-4 py-3">
            <span className="flex-1 pl-[56px] text-[15px] font-medium text-ink">Eslatma vaqti</span>
            <input type="time" value={u.reminder_time} disabled={saving}
              onChange={(e) => e.target.value && update({ reminder_time: e.target.value })}
              className="rounded-full border border-line-strong bg-surface px-3 py-1.5 text-[15px] font-semibold text-ink outline-none focus:border-peri" />
          </div>
        )}
      </Card>

      {u.is_admin && (
        <Card className="overflow-hidden">
          <ListRow title="Admin panel" subtitle="Faktlar, savollar, import, imtihon formati"
            icon={<IconTile tone="muted"><Shield size={20} /></IconTile>} onClick={() => go("/admin")} />
        </Card>
      )}
    </Screen>
  );
}
