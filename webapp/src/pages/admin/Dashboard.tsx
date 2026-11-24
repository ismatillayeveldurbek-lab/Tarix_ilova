import { useEffect, useState } from "react";
import { Loading, Progress, toast } from "../../components/ui";
import { api } from "../../lib/api";
import { navigate } from "../../lib/router";
import { DIFFICULTY } from "./shared";

type Stats = {
  users: number; active_week: number; questions: number; questions_inactive: number;
  answers_today: number; answers_total: number; accuracy: number; reports_new: number; history_events: number;
  by_difficulty: Record<string, number>; by_period: { name: string; count: number }[];
};

export function Dashboard() {
  const [s, setS] = useState<Stats | null>(null);
  useEffect(() => { api<Stats>("/admin/stats").then(setS).catch((e) => toast(e.message, "error")); }, []);
  if (!s) return <Loading />;
  const maxPeriod = Math.max(1, ...s.by_period.map((p) => p.count));
  const tiles: [string, number | string, string][] = [
    ["Foydalanuvchilar", s.users, "var(--blue)"],
    ["7 kunda faol", s.active_week, "var(--green)"],
    ["Faol savollar", s.questions, "var(--purple)"],
    ["Bugungi javoblar", s.answers_today, "var(--orange)"],
    ["O'rtacha aniqlik", `${s.accuracy}%`, "var(--gold)"],
    ["Yangi xato xabarlari", s.reports_new, "var(--red)"],
  ];
  return (
    <div className="stack">
      <h1>Statistika</h1>
      <div className="stat-grid">
        {tiles.map(([l, v, c]) => (
          <div key={l} className="stat-card" style={{ "--c": c } as React.CSSProperties}><div className="v">{v}</div><div className="l">{l}</div></div>
        ))}
      </div>
      {s.questions === 0 && (
        <div className="card row" style={{ borderColor: "var(--green)", background: "var(--green-soft)" }}>
          <div className="grow"><b>Bazada savol yo'q.</b> Excel yoki CSV fayldan savollarni yuklang.</div>
          <button className="btn sm" onClick={() => navigate("/admin/import")}>Import</button>
        </div>
      )}
      <div className="grid-2">
        <div className="card stack">
          <div className="bold">Davrlar bo'yicha savollar</div>
          <div className="bars">
            {s.by_period.map((p) => (
              <div key={p.name} className="bar-row"><span>{p.name}</span><Progress value={p.count / maxPeriod} thin /><span className="bold">{p.count}</span></div>
            ))}
            {s.by_period.length === 0 && <div className="muted small">Ma'lumot yo'q</div>}
          </div>
        </div>
        <div className="card stack">
          <div className="bold">Qiyinlik bo'yicha</div>
          <div className="bars">
            {[1, 2, 3].map((d) => (
              <div key={d} className="bar-row">
                <span>{"★".repeat(d)} {DIFFICULTY[d]}</span>
                <Progress value={(s.by_difficulty[d] || 0) / Math.max(1, s.questions)} thin color={["", "var(--green)", "var(--gold)", "var(--red)"][d]} />
                <span className="bold">{s.by_difficulty[d] || 0}</span>
              </div>
            ))}
          </div>
          <div className="small muted">O'chirilgan savollar: {s.questions_inactive} · "Tarixda bugun" voqealari: {s.history_events} · Jami javoblar: {s.answers_total}</div>
        </div>
      </div>
    </div>
  );
}
