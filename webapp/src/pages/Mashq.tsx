import { useState } from "react";
import { Card, IconTile, ListRow, Pill, Screen, SectionTitle, cx, fmt } from "../components/kit";
import {
  Book, Calendar, ChevronRight, Clipboard, Layers, Lightning, MapPin, Refresh, Scroll, Sparkle, Swords, Target, User,
} from "../components/Icons";
import { navigate } from "../lib/router";
import { useStore } from "../lib/store";
import { haptic } from "../lib/telegram";
import type { FactPath, PeriodNode } from "../lib/types";
import { useApi } from "../lib/useApi";

const go = (to: string) => { haptic.tap(); navigate(to); };

const SECTION_ICONS: Record<string, React.ReactNode> = {
  sana: <Calendar size={20} />, shaxs: <User size={20} />, atama: <Book size={20} />,
  joy: <MapPin size={20} />, urush: <Swords size={20} />, asar: <Scroll size={20} />,
};
const ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"];

/** Kurs dasturi: davr (ochiladigan) va uning mavzulari bo‘yicha testlar */
function Unit({ period, index }: { period: PeriodNode; index: number }) {
  const [open, setOpen] = useState(index === 0);
  const solved = period.topics.reduce((s, t) => s + t.solved, 0);
  const total = period.topics.reduce((s, t) => s + t.total, 0);
  const pct = total ? Math.round((100 * solved) / total) : 0;
  return (
    <Card className="overflow-hidden">
      <button type="button" onClick={() => setOpen(!open)} className="flex w-full items-center gap-3 p-4 text-left">
        <span className="grid h-11 w-11 shrink-0 place-items-center rounded-[14px] bg-peri-soft text-[16px] font-extrabold text-peri">
          {period.id ? ROMAN[index] ?? index + 1 : "—"}
        </span>
        <span className="min-w-0 flex-1">
          <span className="block truncate text-[16px] font-bold text-ink">{period.name}</span>
          <span className="text-[13px] text-muted">{period.topics.length} mavzu · {pct}% o‘zlashtirilgan</span>
        </span>
        <ChevronRight size={18} className={cx("text-faint transition-transform", open && "rotate-90")} />
      </button>
      {open && (
        <div className="divide-y divide-line border-t border-line">
          <ListRow title="Butun davr bo‘yicha test" subtitle={`${total} savol`}
            icon={<IconTile tone="peri" size={36}><Layers size={17} /></IconTile>}
            onClick={() => go(period.id ? `/lesson?mode=period&id=${period.id}` : "/lesson?mode=mixed")} />
          {period.topics.map((t, i) => (
            <ListRow key={t.id} title={t.name} subtitle={`${t.solved}/${t.total} savol`}
              icon={<span className={cx("grid h-9 w-9 shrink-0 place-items-center rounded-full border-2 text-[12px] font-bold",
                t.percent >= 100 ? "border-success bg-success text-white" : t.solved ? "border-peach text-peach" : "border-line-strong text-faint")}>
                {t.percent >= 100 ? "✓" : i + 1}</span>}
              right={<span className="text-[13px] font-semibold text-muted">{t.percent}%</span>}
              onClick={() => go(`/lesson?mode=topic&id=${t.id}`)} />
          ))}
        </div>
      )}
    </Card>
  );
}

export function MashqPage() {
  const { home } = useStore();
  const { data: path } = useApi<FactPath>("/v1/path");
  if (!home) return null;

  return (
    <Screen>
      <header className="px-1">
        <h1 className="text-[28px] font-extrabold tracking-tight text-ink">Mashq</h1>
        <p className="text-[14px] text-muted">Darsliklardagi faktlar, testlar va sinov imtihoni</p>
      </header>

      {/* Qo‘llanma: faktlar bo‘limlari */}
      <SectionTitle right={path ? `${fmt(path.total)} fakt` : undefined}>Qo‘llanma</SectionTitle>
      <div className="grid grid-cols-2 gap-3">
        {(path?.sections ?? []).map((s) => (
          <Card key={s.tur} className="p-4">
            <div className="flex items-start justify-between">
              <IconTile tone={s.tur}>{SECTION_ICONS[s.tur]}</IconTile>
              <Pill className="bg-surface-2 text-faint">Tez orada</Pill>
            </div>
            <div className="mt-3 text-[16px] font-bold text-ink">{s.label}</div>
            <div className="text-[13px] text-muted">{fmt(s.total)} ta</div>
          </Card>
        ))}
        {!path && Array.from({ length: 6 }, (_, i) => <div key={i} className="h-[124px] animate-pulse rounded-card bg-surface-2" />)}
      </div>

      {/* Testlar */}
      <SectionTitle>Testlar</SectionTitle>
      <Card className="divide-y divide-line overflow-hidden">
        <ListRow title={`Kunlik ${home.today.goal} savol`} subtitle={`${Math.min(home.today.done, home.today.goal)} / ${home.today.goal} bajarildi`}
          icon={<IconTile tone="peach"><Lightning size={20} /></IconTile>} onClick={() => go("/lesson?mode=daily")} />
        <ListRow title="Xatolar ustida ishlash" subtitle={home.due_count ? `${home.due_count} ta savol kutmoqda` : "Hozircha xato savol yo‘q"}
          icon={<IconTile tone="danger"><Refresh size={20} /></IconTile>} onClick={() => go("/lesson?mode=review")} />
        <ListRow title="Aralash test" subtitle="Barcha davrlardan 10 ta savol"
          icon={<IconTile tone="atama"><Sparkle size={20} /></IconTile>} onClick={() => go("/lesson?mode=mixed")} />
        <ListRow title="Sinov imtihoni" subtitle={home.exam ? `${home.exam.count} savol · ${home.exam.minutes} daqiqa · taymer bilan` : "Format hali sozlanmagan"}
          icon={<IconTile tone="shaxs"><Clipboard size={20} /></IconTile>} onClick={() => go("/exam")} />
      </Card>

      {/* O‘yinlar */}
      <SectionTitle>O‘yinlar</SectionTitle>
      <Card className="flex items-center gap-3 p-4">
        <IconTile tone="sana"><Target size={20} /></IconTile>
        <div className="min-w-0 flex-1">
          <div className="text-[15.5px] font-semibold text-ink">Qaysi biri oldin?</div>
          <div className="text-[13px] text-muted">60 soniya · ikki voqeadan oldingisini toping</div>
        </div>
        <Pill>Tez orada</Pill>
      </Card>

      {/* Kurs dasturi */}
      <SectionTitle right={`${home.mastery}%`}>Kurs dasturi</SectionTitle>
      {home.path.length === 0 && (
        <Card className="p-5 text-center text-[14px] text-muted">Hozircha test savollari qo‘shilmagan.</Card>
      )}
      {home.path.map((p, i) => <Unit key={p.id} period={p} index={i} />)}
    </Screen>
  );
}
