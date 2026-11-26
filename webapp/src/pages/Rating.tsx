import { useEffect, useState } from "react";
import { Trophy } from "../components/Icons";
import { Avatar, Loading, toast } from "../components/ui";
import { api } from "../lib/api";

type Row = { rank: number; name: string; xp: number; is_me: boolean };
type Data = { rows: Row[]; me: { rank: number | null; xp: number } };

function daysLeft(): number {
  const d = new Date().getDay(); // 0 — yakshanba
  return d === 0 ? 1 : 8 - d;
}

function Rank({ n }: { n: number }) {
  return n <= 3 ? <span className={`medal m${n}`}>{n}</span> : <span className="rank">{n}</span>;
}

export function RatingPage() {
  const [data, setData] = useState<Data | null>(null);
  useEffect(() => { api<Data>("/rating").then(setData).catch((e) => toast(e.message, "error")); }, []);
  if (!data) return <Loading />;

  return (
    <div className="page stack">
      <div className="page-head">
        <div>
          <div className="eyebrow">Haftalik reyting</div>
          <h1>Yetakchilar</h1>
        </div>
        <span className="chip">{daysLeft()} kun qoldi</span>
      </div>

      <div className="metrics" style={{ gridTemplateColumns: "1fr 1fr" }}>
        <div className="metric"><span className="label">Sizning o‘rningiz</span><span className="value">{data.me.rank ?? "—"}</span></div>
        <div className="metric"><span className="label">Bu hafta</span><span className="value">{data.me.xp}<small>XP</small></span></div>
      </div>

      {data.rows.length === 0 ? (
        <div className="card empty">
          <span className="empty-icon"><Trophy size={24} /></span>
          <div className="muted small">Bu hafta hali hech kim savol yechmadi. Birinchi bo‘ling.</div>
        </div>
      ) : (
        <div className="card list" style={{ padding: "4px 10px" }}>
          {data.rows.map((r) => (
            <div key={r.rank} className={`list-row ${r.is_me ? "me" : ""}`}>
              <Rank n={r.rank} />
              <Avatar name={r.name} />
              <span className="grow ellipsis" style={{ fontWeight: r.is_me ? 600 : 500 }}>
                {r.name}{r.is_me && <span className="muted"> (siz)</span>}
              </span>
              <span className="num bold">{r.xp} <span className="tiny muted">XP</span></span>
            </div>
          ))}
        </div>
      )}
      <div className="tiny muted center">To‘g‘ri javob — 10 XP, noto‘g‘ri — 1 XP. Reyting har dushanba yangilanadi.</div>
    </div>
  );
}
