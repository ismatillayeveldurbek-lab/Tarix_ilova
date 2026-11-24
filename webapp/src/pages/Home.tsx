import { TopBar } from "../components/TopBar";
import { Book, Calendar, ChevronRight, Clipboard, Crown, Lightning, Refresh, Star } from "../components/Icons";
import { Mascot } from "../components/Mascot";
import { Progress, Ring } from "../components/ui";
import { navigate } from "../lib/router";
import { useStore } from "../lib/store";
import type { PeriodNode } from "../lib/types";
import { haptic } from "../lib/telegram";

// Har bir davr o'z rangida
const UNIT_COLORS: [string, string][] = [
  ["var(--green)", "var(--green-dark)"],
  ["var(--purple)", "var(--purple-dark)"],
  ["var(--blue)", "var(--blue-dark)"],
  ["var(--orange)", "var(--orange-dark)"],
  ["#14b8a6", "#0f8a7d"],
  ["var(--red)", "var(--red-dark)"],
];
// Tugunlar ilon izi bo'ylab joylashadi
const OFFSETS = [0, 52, 76, 52, 0, -52, -76, -52];

function Unit({ period, index }: { period: PeriodNode; index: number }) {
  const { t } = useStore();
  const [c, cd] = UNIT_COLORS[index % UNIT_COLORS.length];
  const solved = period.topics.reduce((s, x) => s + x.solved, 0);
  const total = period.topics.reduce((s, x) => s + x.total, 0);
  return (
    <section>
      <button className="unit-banner card tap colored" style={{ background: c, "--cd": cd } as React.CSSProperties}
        onClick={() => { haptic.tap(); navigate(period.id ? `/lesson?mode=period&id=${period.id}` : "/lesson?mode=mixed"); }}>
        <div className="row between">
          <div className="grow">
            <div className="tiny">{period.id ? t(`${index + 1}-bo'lim`) : t("Qo'shimcha")}</div>
            <h2>{period.name}</h2>
            <div className="small" style={{ opacity: 0.9, marginTop: 4 }}>{t(`${solved} / ${total} savol yechilgan`)}</div>
          </div>
          <div className="icon-bubble" style={{ width: 48, height: 48, borderRadius: 14, background: "rgba(255,255,255,.22)", display: "grid", placeItems: "center" }}>
            <Book size={26} />
          </div>
        </div>
      </button>
      <div className="path">
        {period.topics.map((topic, i) => {
          const pct = topic.total ? topic.solved / topic.total : 0;
          const done = topic.total > 0 && topic.solved >= topic.total;
          return (
            <div key={topic.id} className="path-node" style={{ transform: `translateX(${OFFSETS[i % OFFSETS.length]}px)` }}>
              <button className={`node-btn ${done ? "done" : ""}`} style={{ "--c": c, "--cd": cd } as React.CSSProperties}
                onClick={() => { haptic.tap(); navigate(`/lesson?mode=topic&id=${topic.id}`); }} aria-label={topic.name}>
                <span className="ring">
                  <Ring value={pct} size={96} stroke={7} color={done ? "var(--gold)" : c} />
                </span>
                <span className="disc">{done ? <Crown size={34} /> : <Star size={34} />}</span>
              </button>
              <div className="node-label">
                {topic.name}
                <div className="muted tiny">{topic.solved}/{topic.total}</div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

export function HomePage() {
  const { home, t } = useStore();
  if (!home) return null;
  const { done, goal } = home.today;
  const goalDone = done >= goal;
  const firstName = home.user.name.split(" ")[0] || "";

  return (
    <>
      <TopBar />
      <div className="page stack">
        {/* Salomlashish */}
        <div className="row" style={{ gap: 4 }}>
          <Mascot size={92} mood={goalDone ? "wow" : "happy"} className="bob" />
          <div className="bubble left grow">
            <div className="bold">{t(firstName ? `Salom, ${firstName}!` : "Salom!")}</div>
            <div className="small muted">
              {goalDone
                ? t("Bugungi maqsad bajarildi! Zo'r ish 🎉")
                : done > 0
                  ? t(`Yana ${goal - done} ta savol — va bugungi maqsad bajariladi!`)
                  : t(`Bugun ${goal} ta savol yechib, ketma-ketlikni davom ettiring.`)}
            </div>
          </div>
        </div>

        {/* Kunlik mashq */}
        <button className="card tap colored green feature" onClick={() => { haptic.tap(); navigate("/lesson?mode=daily"); }}>
          <div className="icon-bubble">{goalDone ? <span className="goal-chest">🏆</span> : <Lightning size={30} />}</div>
          <div className="grow stack" style={{ gap: 6 }}>
            <h3>{goalDone ? t("Maqsad bajarildi!") : t("Kunlik mashq")}</h3>
            <Progress value={done / goal} onColor />
            <div className="small muted">{t(`${Math.min(done, goal)} / ${goal} savol`)}</div>
          </div>
          <ChevronRight />
        </button>

        <div className="grid-2" style={{ gridTemplateColumns: "1fr 1fr" }}>
          <button className={`card tap colored orange ${home.due_count ? "" : "disabled"}`}
            onClick={() => { haptic.tap(); navigate("/lesson?mode=review"); }}>
            <Refresh size={28} />
            <h3 style={{ fontSize: 16, marginTop: 8 }}>{t("Xatolar ustida ishlash")}</h3>
            <div className="small muted">{home.due_count ? t(`${home.due_count} ta savol kutmoqda`) : t("Hozircha yo'q")}</div>
          </button>
          <button className="card tap colored purple" onClick={() => { haptic.tap(); navigate("/exam"); }}>
            <Clipboard size={28} />
            <h3 style={{ fontSize: 16, marginTop: 8 }}>{t("Sinov imtihoni")}</h3>
            <div className="small muted">
              {home.exam ? t(`${home.exam.count} savol · ${home.exam.minutes} daqiqa`) : t("Tez orada")}
            </div>
          </button>
        </div>

        {/* Tarixda bugun */}
        {home.history_today.length > 0 && (
          <div className="card" style={{ borderColor: "var(--blue)", background: "var(--blue-soft)" }}>
            <div className="row" style={{ color: "var(--blue)", marginBottom: 6 }}>
              <Calendar size={22} /><span className="bold">{t("Tarixda bugun")}</span>
            </div>
            <div className="stack" style={{ gap: 8 }}>
              {home.history_today.map((e, i) => (
                <div key={i}>
                  <div className="bold">{e.year ? `${e.year} · ` : ""}{e.title}</div>
                  {e.text && <div className="small muted">{e.text}</div>}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Mavzular yo'li */}
        <div className="section-title" style={{ marginTop: 12 }}>{t("Mavzular")}</div>
        {home.path.length === 0 && (
          <div className="card empty">
            <Mascot mood="think" size={90} />
            <div className="muted">{t("Hozircha savollar qo'shilmagan. Admin panel orqali savollar yuklang.")}</div>
          </div>
        )}
        {home.path.map((p, i) => <Unit key={p.id} period={p} index={i} />)}
        <button className="btn white block" onClick={() => navigate("/lesson?mode=mixed")}>
          {t("Aralash test")}
        </button>
      </div>
    </>
  );
}
