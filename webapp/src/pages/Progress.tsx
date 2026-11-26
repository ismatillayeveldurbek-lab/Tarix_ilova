import { useEffect, useState } from "react";
import { CountUp } from "../components/CountUp";
import { Check, ChevronRight, Target } from "../components/Icons";
import { Bar, Card, IconTile, Screen, SectionTitle, cx } from "../components/kit";
import { ProgressRing } from "../components/motion";
import { Loading, toast } from "../components/ui";
import { api } from "../lib/api";
import { navigate } from "../lib/router";
import { haptic } from "../lib/telegram";
import type { Progress, TopicProgress } from "../lib/types";

/** Foizga qarab rang: qizil < 40 ≤ shaftoli < 80 ≤ yashil */
const level = (p: number) => (p >= 80 ? { text: "text-success", bar: "bg-success", css: "var(--success)" }
  : p >= 40 ? { text: "text-peach", bar: "bg-peach", css: "var(--accent)" }
  : { text: "text-danger", bar: "bg-danger", css: "var(--danger)" });

const open = (id: number) => { haptic.tap(); navigate(`/lesson?mode=topic&id=${id}`); };

function TopicRow({ t }: { t: TopicProgress }) {
  const lv = level(t.percent);
  return (
    <button type="button" onClick={() => open(t.id)}
      className="flex w-full items-center gap-3 px-4 py-3.5 text-left transition hover:bg-surface-2/60 active:bg-surface-2">
      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-between gap-2">
          <span className="truncate text-[15px] font-semibold text-ink">{t.name}</span>
          <span className={cx("text-[14px] font-bold tabular-nums", t.answered ? lv.text : "text-faint")}>{t.percent}%</span>
        </div>
        <Bar value={t.percent / 100} className="mt-2 h-1.5" tone={lv.bar} />
        <div className="mt-1.5 text-[12.5px] text-muted">
          {t.mastered}/{t.total} o‘zlashtirilgan
          {t.accuracy !== null && <> · aniqlik {t.accuracy}%</>}
          {t.answered === 0 && <> · hali boshlanmagan</>}
        </div>
      </div>
      <ChevronRight size={18} className="shrink-0 text-faint" />
    </button>
  );
}

export function ProgressPage() {
  const [data, setData] = useState<Progress | null>(null);
  useEffect(() => { api<Progress>("/progress").then(setData).catch((e) => toast(e.message, "error")); }, []);
  if (!data) return <Loading />;
  const lv = level(data.overall);

  return (
    <Screen>
      <Card className="flex items-center gap-5 p-5">
        <ProgressRing value={data.overall / 100} size={104} stroke={9} tone={lv.css}>
          <span className="text-[26px] font-extrabold tabular-nums text-ink"><CountUp value={data.overall} suffix="%" /></span>
        </ProgressRing>
        <div className="min-w-0">
          <div className="text-[12px] font-bold uppercase tracking-[.12em] text-muted">Natijalar</div>
          <h1 className="text-[24px] font-extrabold tracking-tight text-ink">O‘zlashtirish</h1>
          <div className="text-[13.5px] text-muted">{data.mastered} / {data.total} savolga oxirgi javobingiz to‘g‘ri</div>
        </div>
      </Card>

      {data.weak.length > 0 ? (
        <Card className="overflow-hidden border-danger/30">
          <div className="flex items-center gap-3 px-4 pt-4">
            <IconTile tone="danger" size={40}><Target size={19} /></IconTile>
            <div>
              <div className="text-[16px] font-bold text-ink">Zaif mavzular</div>
              <div className="text-[13px] text-muted">Aniqlik 70% dan past — mashq qilib mustahkamlang</div>
            </div>
          </div>
          <div className="mt-2 divide-y divide-line">
            {data.weak.map((w) => (
              <button key={w.id} type="button" onClick={() => open(w.id)}
                className="flex w-full items-center gap-3 px-4 py-3 text-left transition hover:bg-surface-2/60 active:bg-surface-2">
                <span className="min-w-0 flex-1 truncate text-[15px] font-semibold text-ink">{w.name}</span>
                <span className="rounded-full bg-danger-soft px-2.5 py-0.5 text-[13px] font-bold tabular-nums text-danger">{w.accuracy}%</span>
                <ChevronRight size={18} className="text-faint" />
              </button>
            ))}
          </div>
        </Card>
      ) : data.overall > 0 ? (
        <Card className="flex items-center gap-3 p-4">
          <IconTile tone="success"><Check size={20} /></IconTile>
          <div className="text-[15px] font-semibold text-ink">Zaif mavzu yo‘q — barcha mavzularda aniqlik 70% dan yuqori</div>
        </Card>
      ) : null}

      {data.periods.map((g) => (
        <div key={g.id} className="space-y-2">
          <SectionTitle right={<span className={level(g.percent).text}>{g.percent}%</span>}>{g.name}</SectionTitle>
          <Card className="divide-y divide-line overflow-hidden">
            {g.topics.map((t) => <TopicRow key={t.id} t={t} />)}
          </Card>
        </div>
      ))}
      <p className="px-2 text-center text-[12.5px] text-muted">
        O‘zlashtirish — oxirgi javobi to‘g‘ri bo‘lgan savollar ulushi. Aniqlik — oxirgi 60 kundagi javoblar bo‘yicha.
      </p>
    </Screen>
  );
}
