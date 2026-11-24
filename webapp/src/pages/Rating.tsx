import { useEffect, useState } from "react";
import { Trophy } from "../components/Icons";
import { Mascot } from "../components/Mascot";
import { Avatar, Loading, toast } from "../components/ui";
import { api } from "../lib/api";

type Row = { rank: number; name: string; xp: number; is_me: boolean };
type Data = { rows: Row[]; me: { rank: number | null; xp: number } };

function daysLeft(): number {
  const d = new Date().getDay(); // 0 — yakshanba
  return d === 0 ? 1 : 8 - d;
}

export function RatingPage() {
  const [data, setData] = useState<Data | null>(null);
  useEffect(() => { api<Data>("/rating").then(setData).catch((e) => toast(e.message, "error")); }, []);
  if (!data) return <Loading />;

  const top = data.rows.slice(0, 3);
  const podium = [top[1], top[0], top[2]];
  const heights = [86, 116, 66];
  const colors = ["#9aa7b0", "var(--gold)", "#cd7f32"];

  return (
    <div className="page stack">
      <div className="center stack" style={{ alignItems: "center", gap: 4 }}>
        <div style={{ color: "var(--gold)" }}><Trophy size={44} /></div>
        <h1 style={{ fontSize: 24 }}>Haftalik reyting</h1>
        <div className="small muted">{`Hafta yakunlanishiga ${daysLeft()} kun qoldi`}</div>
      </div>

      {data.rows.length === 0 ? (
        <div className="card empty"><Mascot mood="think" /><div className="muted">Bu hafta hali hech kim savol yechmadi. Birinchi bo'ling!</div></div>
      ) : (
        <>
          <div className="podium">
            {podium.map((r, i) => r ? (
              <div key={r.rank} className="place pop" style={{ animationDelay: `${i * 0.1}s` }}>
                <Avatar name={r.name} size={r.rank === 1 ? "lg" : ""} seed={r.rank} />
                <div className="small bold" style={{ maxWidth: "100%", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.name}</div>
                <div className="tiny bold" style={{ color: "var(--gold-dark)" }}>{r.xp} XP</div>
                <div className="block" style={{ height: heights[i], background: colors[i] }}>{r.rank}</div>
              </div>
            ) : <div key={i} />)}
          </div>
          <div className="card list" style={{ padding: 8 }}>
            {data.rows.map((r) => (
              <div key={r.rank} className={`list-row ${r.is_me ? "me" : ""}`}>
                <span className="rank">{r.rank}</span>
                <Avatar name={r.name} seed={r.rank} />
                <span className="grow bold">{r.name}{r.is_me ? ` ($siz)` : ""}</span>
                <span className="bold" style={{ color: "var(--gold-dark)" }}>{r.xp} XP</span>
              </div>
            ))}
          </div>
        </>
      )}
      <div className="card row">
        <div className="grow">
          <div className="bold">{data.me.rank ? `Sizning o'rningiz: ${data.me.rank}` : "Siz bu hafta hali savol yechmadingiz"}</div>
          <div className="small muted">To'g'ri javob — 10 XP, noto'g'ri — 1 XP</div>
        </div>
        <span className="chip gold" style={{ fontSize: 15 }}>{data.me.xp} XP</span>
      </div>
    </div>
  );
}
