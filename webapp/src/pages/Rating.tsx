import { useEffect, useState } from "react";
import { CountUp } from "../components/CountUp";
import { Trophy } from "../components/Icons";
import { Card, Initials, Pill, Screen, cx } from "../components/kit";
import { Loading, toast } from "../components/ui";
import { api } from "../lib/api";

type Row = { rank: number; name: string; xp: number; is_me: boolean };
type Data = { rows: Row[]; me: { rank: number | null; xp: number } };

function daysLeft(): number {
  const d = new Date().getDay(); // 0 — yakshanba
  return d === 0 ? 1 : 8 - d;
}

const MEDAL = ["", "bg-[#f5c542] text-[#5a4300]", "bg-[#cfd6e2] text-[#3a4458]", "bg-[#e7a977] text-[#5b2f10]"];
const PODIUM_H = ["", "h-[92px]", "h-[68px]", "h-[52px]"];
const BAR = ["", "bg-[linear-gradient(180deg,#f8d877,#f5c542)] text-[#5a4300]", "bg-surface-2 text-muted", "bg-peach-soft text-peach"];

/** Top-3 shohsupa: ustunlar pastdan o‘sib chiqadi */
function Podium({ rows }: { rows: Row[] }) {
  const order = [rows[1], rows[0], rows[2]].filter(Boolean);
  return (
    <div className="flex items-end justify-center gap-3 px-2 pt-2">
      {order.map((r, i) => (
        <div key={r.rank} className="flex w-[30%] animate-rise flex-col items-center" style={{ animationDelay: `${[150, 0, 300][i]}ms` }}>
          <div className="relative">
            <Initials name={r.name} size={r.rank === 1 ? 62 : 52} />
            <span className={cx("absolute -bottom-1 -right-1 grid h-6 w-6 animate-pop place-items-center rounded-full text-[12px] font-extrabold ring-2 ring-surface", MEDAL[r.rank])}
              style={{ animationDelay: `${400 + i * 120}ms` }}>{r.rank}</span>
          </div>
          <div className={cx("mt-2 w-full truncate text-center text-[13.5px] font-semibold", r.is_me ? "text-peri" : "text-ink")}>
            {r.name.split(" ")[0]}{r.is_me && " (siz)"}
          </div>
          <div className="text-[13px] font-bold tabular-nums text-muted">{r.xp} XP</div>
          <div className={cx("mt-2 grid w-full origin-bottom animate-grow place-items-center rounded-t-2xl",
            BAR[r.rank], PODIUM_H[r.rank])} style={{ animationDelay: `${200 + i * 100}ms` }}>
            <span className="text-[22px] font-extrabold opacity-60">{r.rank}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

export function RatingPage() {
  const [data, setData] = useState<Data | null>(null);
  useEffect(() => { api<Data>("/rating").then(setData).catch((e) => toast(e.message, "error")); }, []);
  if (!data) return <Loading />;
  const rest = data.rows.slice(3);

  return (
    <Screen>
      <header className="flex items-end justify-between px-1">
        <div>
          <div className="text-[12px] font-bold uppercase tracking-[.12em] text-muted">Haftalik reyting</div>
          <h1 className="text-[28px] font-extrabold tracking-tight text-ink">Yetakchilar</h1>
        </div>
        <Pill className="bg-peach-soft text-peach">{daysLeft()} kun qoldi</Pill>
      </header>

      <div className="grid grid-cols-2 gap-3">
        <Card className="p-4">
          <div className="text-[12.5px] font-semibold text-muted">Sizning o‘rningiz</div>
          <div className="mt-0.5 text-[28px] font-extrabold tabular-nums text-ink">{data.me.rank ? <CountUp value={data.me.rank} /> : "—"}</div>
        </Card>
        <Card className="p-4">
          <div className="text-[12.5px] font-semibold text-muted">Bu hafta</div>
          <div className="mt-0.5 text-[28px] font-extrabold tabular-nums text-ink"><CountUp value={data.me.xp} /> <span className="text-[14px] text-muted">XP</span></div>
        </Card>
      </div>

      {data.rows.length === 0 ? (
        <Card className="flex flex-col items-center gap-2 p-8 text-center">
          <span className="grid h-14 w-14 animate-pop place-items-center rounded-2xl bg-sana-soft text-sana"><Trophy size={26} /></span>
          <div className="text-[15px] font-semibold text-ink">Bu hafta hali hech kim mashq qilmadi</div>
          <div className="text-[13.5px] text-muted">Birinchi bo‘ling.</div>
        </Card>
      ) : (
        <>
          <Card className="overflow-hidden pt-3"><Podium rows={data.rows.slice(0, 3)} /></Card>
          {rest.length > 0 && (
            <Card className="stagger divide-y divide-line overflow-hidden">
              {rest.map((r) => (
                <div key={r.rank} className={cx("flex items-center gap-3 px-4 py-3", r.is_me && "bg-peri-soft")}>
                  <span className="w-6 text-center text-[14px] font-bold tabular-nums text-muted">{r.rank}</span>
                  <Initials name={r.name} size={38} />
                  <span className={cx("min-w-0 flex-1 truncate text-[15px]", r.is_me ? "font-bold text-peri" : "font-medium text-ink")}>
                    {r.name}{r.is_me && " (siz)"}
                  </span>
                  <span className="text-[14px] font-bold tabular-nums text-ink">{r.xp} <span className="text-[11px] text-muted">XP</span></span>
                </div>
              ))}
            </Card>
          )}
        </>
      )}
      <p className="px-2 text-center text-[12.5px] text-muted">
        Haftalik XP: testlar, kartochkalar, o‘yinlar va do‘st takliflari. Reyting har dushanba yangilanadi.
      </p>
    </Screen>
  );
}
