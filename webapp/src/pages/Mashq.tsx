import { useState } from "react";
import { Bar, Card, HeroCard, IconTile, ListRow, Pill, Screen, SectionTitle, cx, fmt } from "../components/kit";
import {
  Book, Calendar, ChevronRight, Clipboard, Layers, Lightning, MapPin, Refresh, Scroll, Sparkle, Swords, User,
} from "../components/Icons";
import { navigate } from "../lib/router";
import { useStore } from "../lib/store";
import { haptic } from "../lib/telegram";
import type { CardsSummary, FactPath, PeriodNode, TopicNode } from "../lib/types";
import { useApi } from "../lib/useApi";

const go = (to: string) => { haptic.tap(); navigate(to); };

const SECTION_ICONS: Record<string, React.ReactNode> = {
  sana: <Calendar size={20} />, shaxs: <User size={20} />, atama: <Book size={20} />,
  joy: <MapPin size={20} />, urush: <Swords size={20} />, asar: <Scroll size={20} />,
};
// Tailwind klasslarni manba kodidan qidiradi — shuning uchun nomlar to'liq yozilgan
const BAR_TONE: Record<string, string> = {
  sana: "bg-sana", shaxs: "bg-shaxs", atama: "bg-atama", joy: "bg-joy", urush: "bg-urush", asar: "bg-asar",
};
const ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"];

/** Mavzularni darslik bo‘yicha guruhlaydi (server tartibi saqlanadi); darsliksizlar — alohida */
function groupByBook(topics: TopicNode[]): [string, TopicNode[]][] {
  const groups = new Map<string, TopicNode[]>();
  for (const t of topics) {
    const k = t.book ?? "";
    groups.set(k, [...(groups.get(k) ?? []), t]);
  }
  return [...groups.entries()];
}

function TopicRow({ t, n }: { t: TopicNode; n: number }) {
  return (
    <ListRow title={t.name} subtitle={`${t.solved}/${t.total} savol`}
      icon={<span className={cx("grid h-9 w-9 shrink-0 place-items-center rounded-full border-2 text-[12px] font-bold",
        t.percent >= 100 ? "border-success bg-success text-white" : t.solved ? "border-peach text-peach" : "border-line-strong text-faint")}>
        {t.percent >= 100 ? "✓" : n}</span>}
      right={<span className="text-[13px] font-semibold text-muted">{t.percent}%</span>}
      onClick={() => go(`/lesson?mode=topic&id=${t.id}`)} />
  );
}

/** Davr ichidagi darslik: ochiladigan guruh (davrda 100+ mavzu bo‘lsa ham ro‘yxat qisqa) */
function BookGroup({ title, topics }: { title: string; topics: TopicNode[] }) {
  const [open, setOpen] = useState(false);
  const solved = topics.reduce((s, t) => s + t.solved, 0);
  const total = topics.reduce((s, t) => s + t.total, 0);
  return (
    <div>
      <button type="button" onClick={() => { haptic.select(); setOpen(!open); }}
        className="flex w-full items-center gap-3 bg-surface-2/50 px-4 py-3 text-left transition hover:bg-surface-2">
        <Book size={17} className="shrink-0 text-peri" />
        <span className="min-w-0 flex-1">
          <span className="block truncate text-[14.5px] font-bold text-ink">{title}</span>
          <span className="text-[12.5px] text-muted">{topics.length} mavzu · {solved}/{total} savol</span>
        </span>
        <ChevronRight size={16} className={cx("text-faint transition-transform duration-300", open && "rotate-90")} />
      </button>
      {open && (
        <div className="stagger divide-y divide-line">
          {topics.map((t, i) => <TopicRow key={t.id} t={t} n={i + 1} />)}
        </div>
      )}
    </div>
  );
}

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
          {groupByBook(period.topics).map(([book, topics]) => book
            ? <BookGroup key={book} title={book} topics={topics} />
            : topics.map((t, i) => <TopicRow key={t.id} t={t} n={i + 1} />))}
        </div>
      )}
    </Card>
  );
}

export function MashqPage() {
  const { home } = useStore();
  const { data: path } = useApi<FactPath>("/v1/path");
  const { data: srs } = useApi<CardsSummary>("/v1/cards/summary");
  const { data: game } = useApi<{ xp_today: number; xp_cap: number }>("/v1/games/oldin");
  if (!home) return null;

  return (
    <Screen>
      <header className="px-1">
        <h1 className="text-[28px] font-extrabold tracking-tight text-ink">Mashq</h1>
        <p className="text-[14px] text-muted">Darsliklardagi faktlar, testlar va sinov imtihoni</p>
      </header>

      {/* Kunlik takrorlash */}
      <HeroCard onClick={() => go("/cards")}>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-[12px] font-semibold uppercase tracking-[.12em] text-white/65">Kunlik takrorlash</div>
            <div className="mt-1 text-[22px] font-extrabold tracking-tight">
              {!srs ? "Kartalar" : srs.due + srs.new_left === 0 ? "Bugungi kartalar tugadi" : `${srs.due} takrorga · ${srs.new_left} yangi`}
            </div>
            <div className="text-[13px] text-white/65">
              {srs && srs.due + srs.new_left === 0 ? `Ertaga yana ${srs.new_per_day} ta yangi karta` : "Karta → javobni ko‘rish → bildim / bilmadim"}
            </div>
          </div>
          <span className="grid h-11 w-11 place-items-center rounded-2xl bg-white/12"><Refresh size={22} /></span>
        </div>
      </HeroCard>

      {/* Qo‘llanma: faktlar bo‘limlari */}
      <SectionTitle right={path ? `${fmt(path.total)} fakt` : undefined}>Qo‘llanma</SectionTitle>
      <div className="grid grid-cols-2 gap-3">
        {(path?.sections ?? []).map((s) => {
          const st = srs?.sections[s.tur];
          return (
            <Card key={s.tur} className="p-4" onClick={() => go(`/cards?tur=${s.tur}`)}>
              <div className="flex items-start justify-between">
                <IconTile tone={s.tur}>{SECTION_ICONS[s.tur]}</IconTile>
                {st && st.due > 0 && <Pill className="bg-danger-soft text-danger">{st.due} takrorga</Pill>}
              </div>
              <div className="mt-3 text-[16px] font-bold text-ink">{s.label}</div>
              <div className="text-[13px] text-muted">{fmt(st?.mastered ?? 0)} / {fmt(s.total)} o‘zlashtirildi</div>
              <Bar value={st && s.total ? (st.mastered + st.learning * 0.3) / s.total : 0} className="mt-2.5 h-1.5" tone={BAR_TONE[s.tur]} />
            </Card>
          );
        })}
        {!path && Array.from({ length: 6 }, (_, i) => <div key={i} className="h-[124px] animate-pulse rounded-card bg-surface-2" />)}
      </div>

      {/* Testlar */}
      <SectionTitle>Testlar</SectionTitle>
      <Card className="divide-y divide-line overflow-hidden">
        <ListRow title="Kunlik test" subtitle="10 ta savol: takrorlash vaqti kelganlar + yangilari"
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
      <Card className="p-4" onClick={() => go("/oldin")}>
        <div className="flex items-center gap-3">
          <IconTile tone="sana"><Calendar size={20} /></IconTile>
          <div className="min-w-0 flex-1">
            <div className="text-[15.5px] font-semibold text-ink">Qaysi biri oldin?</div>
            <div className="text-[13px] text-muted">60 soniya · ikki voqeadan oldingisini toping</div>
          </div>
          <Pill className={game && game.xp_today >= game.xp_cap ? "bg-success-soft text-success" : "bg-sana-soft text-sana"}>
            {game ? `${game.xp_today}/${game.xp_cap} XP` : "XP"}
          </Pill>
        </div>
        {game && <Bar value={game.xp_today / game.xp_cap} className="mt-3 h-1.5" tone="bg-sana" />}
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
