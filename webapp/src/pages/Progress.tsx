import { useEffect, useState } from "react";
import { ChevronRight } from "../components/Icons";
import { Mascot } from "../components/Mascot";
import { CountUp } from "../components/CountUp";
import { levelColor, Loading, Progress as Bar, Ring, toast } from "../components/ui";
import { api } from "../lib/api";
import { navigate } from "../lib/router";
import { haptic } from "../lib/telegram";
import type { Progress, TopicProgress } from "../lib/types";

function TopicRow({ t }: { t: TopicProgress }) {
  return (
    <button className="topic-row" onClick={() => { haptic.tap(); navigate(`/lesson?mode=topic&id=${t.id}`); }}>
      <div className="grow stack" style={{ gap: 6, minWidth: 0 }}>
        <div className="row between" style={{ gap: 8 }}>
          <span className="bold ellipsis">{t.name}</span>
          <span className="bold" style={{ color: levelColor(t.percent) }}>{t.percent}%</span>
        </div>
        <Bar value={t.percent / 100} thin color={levelColor(t.percent)} />
        <div className="tiny muted">
          {t.mastered}/{t.total} o'zlashtirilgan
          {t.accuracy !== null && <> · aniqlik {t.accuracy}%</>}
          {t.answered === 0 && <> · hali boshlanmagan</>}
        </div>
      </div>
      <ChevronRight size={20} />
    </button>
  );
}

export function ProgressPage() {
  const [data, setData] = useState<Progress | null>(null);
  useEffect(() => { api<Progress>("/progress").then(setData).catch((e) => toast(e.message, "error")); }, []);
  if (!data) return <Loading />;

  return (
    <div className="page stack">
      <div className="card row" style={{ gap: 16 }}>
        <Ring value={data.overall / 100} size={104} stroke={11} color={levelColor(data.overall)}>
          <div className="center"><div style={{ fontSize: 26, fontWeight: 900 }}><CountUp value={data.overall} suffix="%" /></div></div>
        </Ring>
        <div className="grow">
          <h1 style={{ fontSize: 22 }}>O'zlashtirish</h1>
          <div className="small muted">{data.mastered} / {data.total} savolga oxirgi javobingiz to'g'ri</div>
        </div>
      </div>

      {data.weak.length > 0 ? (
        <div className="card stack" style={{ borderColor: "var(--red)", background: "var(--red-soft)", gap: 10 }}>
          <div className="bold" style={{ color: "var(--red)" }}>⚠️ Zaif mavzular</div>
          <div className="small">Bu mavzularda aniqlik 70% dan past. Mashq qilib, mustahkamlang:</div>
          {data.weak.map((w) => (
            <button key={w.id} className="btn red block" style={{ justifyContent: "space-between" }}
              onClick={() => navigate(`/lesson?mode=topic&id=${w.id}`)}>
              <span className="ellipsis" style={{ textTransform: "none", letterSpacing: 0 }}>{w.name}</span>
              <span>{w.accuracy}%</span>
            </button>
          ))}
        </div>
      ) : data.overall > 0 ? (
        <div className="card row" style={{ borderColor: "var(--green)", background: "var(--green-soft)" }}>
          <Mascot size={56} mood="wow" /><div className="bold">Zaif mavzu yo'q — zo'r natija!</div>
        </div>
      ) : null}

      {data.periods.map((g) => (
        <div key={g.id} className="stack" style={{ gap: 8 }}>
          <div className="row between" style={{ marginTop: 8 }}>
            <div className="section-title" style={{ margin: 0 }}>{g.name}</div>
            <span className="chip" style={{ color: levelColor(g.percent) }}>{g.percent}%</span>
          </div>
          <div className="card list" style={{ padding: 4 }}>
            {g.topics.map((t) => <TopicRow key={t.id} t={t} />)}
          </div>
        </div>
      ))}
      <div className="tiny muted center">
        O'zlashtirish — oxirgi javobi to'g'ri bo'lgan savollar ulushi. Aniqlik — oxirgi 60 kundagi javoblar bo'yicha.
      </div>
    </div>
  );
}
