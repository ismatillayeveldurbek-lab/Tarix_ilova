import { CountUp } from "../components/CountUp";
import { Bar, Card, HeroCard, IconTile, Initials, ListRow, Pill, Screen, SectionTitle, cx, fmt } from "../components/kit";
import { Check, ChevronRight, Clipboard, Flame, Lightning, Refresh, Star, Target, Trophy, Users } from "../components/Icons";
import { navigate } from "../lib/router";
import { useStore } from "../lib/store";
import { haptic } from "../lib/telegram";
import type { CardsSummary, FactPath } from "../lib/types";
import { useApi } from "../lib/useApi";

const MONTHS = ["yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr"];
const WEEKDAYS = ["yakshanba", "dushanba", "seshanba", "chorshanba", "payshanba", "juma", "shanba"];
const go = (to: string) => { haptic.tap(); navigate(to); };

/** "Tarix yo‘lingiz": faktlar bo‘yicha umumiy yo‘l va to‘rt davr */
function PathHero({ path, due, xp, done, goal }: { path: FactPath | null; due: number; xp: number; done: number; goal: number }) {
  const pct = path && path.total ? path.mastered / path.total : 0;
  return (
    <HeroCard>
      <div className="flex items-start justify-between">
        <div>
          <div className="text-[12px] font-semibold uppercase tracking-[.12em] text-white/65">Tarix yo‘lingiz</div>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-[34px] font-extrabold leading-none tracking-tight"><CountUp value={path?.mastered ?? 0} /></span>
            <span className="text-[15px] font-semibold text-white/60">/ {fmt(path?.total ?? 0)} fakt</span>
          </div>
          <div className="mt-1 text-[13px] text-white/65">o‘zlashtirildi · {Math.round(pct * 100)}%</div>
        </div>
        <span className="grid h-11 w-11 place-items-center rounded-2xl bg-white/12"><Target size={22} /></span>
      </div>

      {/* To‘rt davr — bekatlar */}
      <div className="mt-5 grid grid-cols-4 gap-2">
        {(path?.davrlar ?? []).slice(0, 4).map((d) => {
          const p = d.total ? d.mastered / d.total : 0;
          return (
            <div key={d.name} className="min-w-0">
              <div className="h-1.5 overflow-hidden rounded-full bg-white/15">
                <div className="h-full rounded-full bg-[#ffe064] transition-[width] duration-1000 ease-out-soft" style={{ width: `${Math.max(p * 100, d.started ? 4 : 0)}%` }} />
              </div>
              <div className="mt-1.5 truncate text-[11.5px] font-semibold text-white/80">{d.name}</div>
              <div className="text-[11px] text-white/50">{fmt(d.total)}</div>
            </div>
          );
        })}
      </div>

      <div className="mt-5 grid grid-cols-3 gap-2">
        {[
          ["Takrorga", fmt(due)],
          ["Bugungi XP", <CountUp key="xp" value={xp} />],
          ["Bugun", `${Math.min(done, goal)}/${goal}`],
        ].map(([label, value]) => (
          <div key={String(label)} className="rounded-2xl bg-white/[.08] px-3 py-2.5">
            <div className="text-[11.5px] font-medium text-white/60">{label}</div>
            <div className="text-[18px] font-bold">{value}</div>
          </div>
        ))}
      </div>
    </HeroCard>
  );
}

export function HomePage() {
  const { home } = useStore();
  const { data: path } = useApi<FactPath>("/v1/path");
  const { data: me } = useApi<{ facts: { due_now: number }; today: { xp: number; cards_reviewed: number } }>("/v1/me");
  const { data: srs } = useApi<CardsSummary>("/v1/cards/summary");
  if (!home) return null;

  const now = new Date();
  const { done, goal } = home.today;
  const firstName = home.user.name.split(" ")[0] || "";
  const rec = home.recommendation;
  const planItems = [
    {
      key: "srs", tone: "peri", icon: <Refresh size={20} />, title: "Kunlik takrorlash",
      sub: srs ? (srs.due + srs.new_left > 0 ? `${srs.due} takrorga · ${srs.new_left} yangi karta` : "Bugungi kartalar tugadi")
        : "Faktlar kartochkasi",
      done: !!srs && srs.due === 0 && srs.new_left === 0, soon: false, to: "/cards",
    },
    {
      key: "daily", tone: "peach", icon: <Lightning size={20} />, title: "Kunlik test",
      sub: "10 ta savol: takrorlash + yangilari", done: false, soon: false, to: "/lesson?mode=daily",
    },
    {
      key: "review", tone: "danger", icon: <Target size={20} />, title: "Xatolar ustida ishlash",
      sub: home.due_count ? `${home.due_count} ta savol kutmoqda` : "Hozircha xato savol yo‘q", done: home.due_count === 0, soon: false, to: "/lesson?mode=review",
    },
    {
      key: "exam", tone: "shaxs", icon: <Clipboard size={20} />, title: "Sinov imtihoni",
      sub: home.exam ? `${home.exam.count} savol · ${home.exam.minutes} daqiqa` : "Tez orada", done: false, soon: !home.exam, to: "/exam",
    },
  ];

  return (
    <Screen>
      {/* Salomlashish */}
      <header className="flex items-center gap-3">
        <Initials name={home.user.name} size={46} />
        <div className="min-w-0 flex-1">
          <div className="truncate text-[21px] font-bold tracking-tight text-ink">Salom{firstName ? `, ${firstName}` : ""}!</div>
          <div className="text-[13px] text-muted">{WEEKDAYS[now.getDay()]}, {now.getDate()}-{MONTHS[now.getMonth()]}</div>
        </div>
        <span className={cx("inline-flex items-center gap-1 rounded-full bg-surface px-3 py-1.5 text-[15px] font-bold shadow-soft",
          home.user.streak ? "text-peach" : "text-faint")}>
          <Flame size={17} className={home.user.streak ? "animate-breathe" : undefined} /> <CountUp value={home.user.streak} duration={600} />
        </span>
      </header>

      <PathHero path={path} due={me?.facts.due_now ?? 0} xp={me?.today.xp ?? 0} done={done} goal={goal} />

      {/* Bugungi reja */}
      <Card className="overflow-hidden">
        <div className="flex items-center justify-between px-4 pt-4 pb-1">
          <div>
            <div className="text-[17px] font-bold text-ink">Bugungi reja</div>
            <div className="text-[13px] text-muted">Kuniga {goal} ta mashq: test, kartochka yoki o‘yin</div>
          </div>
          <Pill className={done >= goal ? "bg-success-soft text-success" : "bg-peri-soft text-peri"}>
            {done >= goal ? "Maqsad bajarildi" : `${Math.min(done, goal)} / ${goal} mashq`}
          </Pill>
        </div>
        <div className="divide-y divide-line">
          {planItems.map((p) => (
            <ListRow key={p.key} title={p.title} subtitle={p.sub} disabled={p.soon}
              icon={<IconTile tone={p.done ? "success" : p.tone}>{p.done ? <Check size={20} /> : p.icon}</IconTile>}
              onClick={p.soon ? undefined : () => go(p.to)}
              right={p.soon ? <Pill>Tez orada</Pill> : undefined} />
          ))}
        </div>
      </Card>

      {/* Tavsiya */}
      {rec && (
        <Card onClick={() => go(`/lesson?mode=topic&id=${rec.id}`)} className="flex items-center gap-3 p-4">
          <IconTile tone={rec.kind === "weak" ? "danger" : "peri"}>{rec.kind === "weak" ? <Target size={20} /> : <Star size={20} />}</IconTile>
          <div className="min-w-0 flex-1">
            <div className="text-[12px] font-semibold uppercase tracking-[.08em] text-muted">
              {rec.kind === "weak" ? "Mustahkamlash kerak" : "Keyingi mavzu"}
            </div>
            <div className="truncate text-[15.5px] font-semibold text-ink">{rec.name}</div>
            <div className="text-[13px] text-muted">{rec.kind === "weak" ? `Aniqlik ${rec.accuracy}%` : `${rec.total} ta savol`}</div>
          </div>
          <ChevronRight size={18} className="text-faint" />
        </Card>
      )}

      {/* Bugun tarixda — taqvim varag‘i */}
      {home.history_today.length > 0 && (
        <Card className="flex gap-4 p-4">
          <div className="w-[68px] shrink-0 overflow-hidden rounded-2xl border border-line text-center">
            <div className="bg-danger py-1 text-[11px] font-bold uppercase tracking-wider text-white">{MONTHS[now.getMonth()].slice(0, 3)}</div>
            <div className="py-1.5 text-[28px] font-extrabold leading-none text-ink">{now.getDate()}</div>
          </div>
          <div className="min-w-0 flex-1 space-y-2">
            <div className="text-[12px] font-semibold uppercase tracking-[.08em] text-muted">Bugun tarixda</div>
            {home.history_today.slice(0, 2).map((e, i) => (
              <div key={i}>
                <div className="text-[15px] font-semibold leading-snug text-ink">{e.year ? `${e.year} · ` : ""}{e.title}</div>
                {e.text && <div className="font-reading text-[14px] leading-relaxed text-ink-2">{e.text}</div>}
              </div>
            ))}
          </div>
        </Card>
      )}

      <div className="grid grid-cols-2 gap-3">
        <Card onClick={() => go("/rating")} className="p-4">
          <IconTile tone="sana"><Trophy size={20} /></IconTile>
          <div className="mt-3 text-[15px] font-bold text-ink">Reyting</div>
          <div className="text-[13px] text-muted">{home.week.rank ? `${home.week.rank}-o‘rin · ${home.week.xp} XP` : "Bu hafta hali yo‘q"}</div>
        </Card>
        <Card onClick={() => go("/invite")} className="p-4">
          <IconTile tone="joy"><Users size={20} /></IconTile>
          <div className="mt-3 text-[15px] font-bold text-ink">Do‘stlarni taklif</div>
          <div className="text-[13px] text-muted">Har do‘st uchun XP</div>
        </Card>
      </div>

      <SectionTitle right={`${home.mastery}%`}>Mavzular bo‘yicha natija</SectionTitle>
      <Card onClick={() => go("/progress")} className="p-4">
        <div className="flex items-center justify-between">
          <span className="text-[15px] font-semibold text-ink">O‘zlashtirish va zaif mavzular</span>
          <ChevronRight size={18} className="text-faint" />
        </div>
        <Bar value={home.mastery / 100} className="mt-3" />
      </Card>
    </Screen>
  );
}
