import { useEffect, useState } from "react";
import { levelColor, Loading, Progress, toast } from "../../components/ui";
import { api } from "../../lib/api";
import { navigate } from "../../lib/router";
import { DIFFICULTY } from "./shared";

type Stats = {
  users: number; active_week: number; questions: number; questions_inactive: number;
  answers_today: number; answers_total: number; accuracy: number; reports_new: number; history_events: number;
  by_difficulty: Record<string, number>; by_period: { name: string; count: number }[];
  hard_topics: { name: string; answers: number; accuracy: number }[];
  referrals: { total: number; active: number; top: { name: string; invited: number; active: number }[] };
};

export function Dashboard() {
  const [s, setS] = useState<Stats | null>(null);
  useEffect(() => { api<Stats>("/admin/stats").then(setS).catch((e) => toast(e.message, "error")); }, []);
  if (!s) return <Loading />;
  const maxPeriod = Math.max(1, ...s.by_period.map((p) => p.count));
  const tiles: [string, number | string, string][] = [
    ["Foydalanuvchilar", s.users, "var(--text)"],
    ["7 kunda faol", s.active_week, "var(--text)"],
    ["Faol savollar", s.questions, "var(--text)"],
    ["Bugungi javoblar", s.answers_today, "var(--text)"],
    ["O'rtacha aniqlik", `${s.accuracy}%`, "var(--text)"],
    ["Yangi xato xabarlari", s.reports_new, s.reports_new ? "var(--danger)" : "var(--text)"],
  ];
  return (
    <div className="stack">
      <h1>Statistika</h1>
      <div className="stat-grid">
        {tiles.map(([l, v, c]) => (
          <div key={l} className="stat-card" style={{ "--c": c } as React.CSSProperties}><div className="v" style={{ color: "var(--c)" }}>{v}</div><div className="l">{l}</div></div>
        ))}
      </div>
      <div className="card stack">
        <div className="row between">
          <div className="bold">Referal (taklif) tizimi</div>
          <div className="row small"><span className="chip blue">Takliflar: {s.referrals.total}</span><span className="chip green">Faol: {s.referrals.active}</span></div>
        </div>
        {s.referrals.top.length === 0 ? <div className="small muted">Hali taklif yo'q</div> : (
          <div className="list">
            {s.referrals.top.map((r, i) => (
              <div key={i} className="list-row"><span className="rank">{i + 1}</span><span className="grow bold">{r.name}</span>
                <span className="small muted">{r.invited} ta taklif · {r.active} ta faol</span></div>
            ))}
          </div>
        )}
      </div>
      {s.questions === 0 && (
        <div className="card row" style={{ borderColor: "var(--success)", background: "var(--success-soft)" }}>
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
                <span>{DIFFICULTY[d]}</span>
                <Progress value={(s.by_difficulty[d] || 0) / Math.max(1, s.questions)} thin color={["", "var(--success)", "var(--accent)", "var(--danger)"][d]} />
                <span className="bold">{s.by_difficulty[d] || 0}</span>
              </div>
            ))}
          </div>
          {s.hard_topics.length > 0 && (
            <>
              <div className="bold" style={{ marginTop: 8 }}>Eng qiyin mavzular (o'quvchilar aniqligi)</div>
              <div className="bars">
                {s.hard_topics.map((h) => (
                  <div key={h.name} className="bar-row">
                    <span>{h.name}</span>
                    <Progress value={h.accuracy / 100} thin color={levelColor(h.accuracy)} />
                    <span className="bold">{h.accuracy}%</span>
                  </div>
                ))}
              </div>
              <div className="small muted">Kamida 10 ta javob berilgan mavzular. Bu mavzularga izoh va savollarni ko'paytirish foydali.</div>
            </>
          )}
          <div className="small muted">O'chirilgan savollar: {s.questions_inactive} · "Tarixda bugun" voqealari: {s.history_events} · Jami javoblar: {s.answers_total}</div>
        </div>
      </div>
    </div>
  );
}
