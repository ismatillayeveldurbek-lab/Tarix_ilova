import { useEffect, useState } from "react";
import { Check, ChevronRight } from "../components/Icons";
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
          {t.mastered}/{t.total} o‘zlashtirilgan
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
        <Ring value={data.overall / 100} size={96} stroke={7} color={levelColor(data.overall)}>
          <div className="center"><div className="serif num" style={{ fontSize: 26, fontWeight: 600 }}><CountUp value={data.overall} suffix="%" /></div></div>
        </Ring>
        <div className="grow">
          <div className="eyebrow">Natijalar</div>
          <h1 style={{ fontSize: 23 }}>O‘zlashtirish</h1>
          <div className="small muted">{data.mastered} / {data.total} savolga oxirgi javobingiz to‘g‘ri</div>
        </div>
      </div>

      {data.weak.length > 0 ? (
        <div className="card stack callout" style={{ "--c": "var(--danger)", gap: 10 } as React.CSSProperties}>
          <div className="eyebrow" style={{ color: "var(--danger)" }}>Zaif mavzular</div>
          <div className="small">Bu mavzularda aniqlik 70% dan past. Mashq qilib, mustahkamlang:</div>
          {data.weak.map((w) => (
            <button key={w.id} className="btn white block" style={{ justifyContent: "space-between" }}
              onClick={() => navigate(`/lesson?mode=topic&id=${w.id}`)}>
              <span className="ellipsis">{w.name}</span>
              <span className="num" style={{ color: "var(--danger)" }}>{w.accuracy}%</span>
            </button>
          ))}
        </div>
      ) : data.overall > 0 ? (
        <div className="card row">
          <span className="icon-box success"><Check size={20} /></span><div className="bold">Zaif mavzu yo‘q — barcha mavzularda aniqlik 70% dan yuqori</div>
        </div>
      ) : null}

      {data.periods.map((g) => (
        <div key={g.id} className="stack" style={{ gap: 8 }}>
          <div className="row between" style={{ marginTop: 8 }}>
            <div className="section-title" style={{ margin: 0 }}>{g.name}</div>
            <span className="num bold small" style={{ color: levelColor(g.percent) }}>{g.percent}%</span>
          </div>
          <div className="card list" style={{ padding: 4 }}>
            {g.topics.map((t) => <TopicRow key={t.id} t={t} />)}
          </div>
        </div>
      ))}
      <div className="tiny muted center">
        O‘zlashtirish — oxirgi javobi to‘g‘ri bo‘lgan savollar ulushi. Aniqlik — oxirgi 60 kundagi javoblar bo‘yicha.
      </div>
    </div>
  );
}
