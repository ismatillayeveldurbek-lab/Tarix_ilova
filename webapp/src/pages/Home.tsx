import { Calendar, ChevronRight, Clipboard, Flame, Refresh, Star, Target, Users } from "../components/Icons";
import { Progress } from "../components/ui";
import { navigate } from "../lib/router";
import { useStore } from "../lib/store";
import { haptic } from "../lib/telegram";
import type { PeriodNode } from "../lib/types";

const ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"];
const MONTHS = ["yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr"];

function greeting(): string {
  const h = new Date().getHours();
  return h < 5 ? "Xayrli tun" : h < 12 ? "Xayrli tong" : h < 18 ? "Xayrli kun" : "Xayrli kech";
}

const go = (to: string) => { haptic.tap(); navigate(to); };

/** Kurs dasturi: bitta davr va uning mavzulari */
function Unit({ period, index }: { period: PeriodNode; index: number }) {
  const solved = period.topics.reduce((s, x) => s + x.solved, 0);
  const total = period.topics.reduce((s, x) => s + x.total, 0);
  const pct = total ? Math.round((100 * solved) / total) : 0;
  return (
    <section className="unit">
      <button className="unit-head" onClick={() => go(period.id ? `/lesson?mode=period&id=${period.id}` : "/lesson?mode=mixed")}>
        <span className="unit-num">{period.id ? ROMAN[index] ?? index + 1 : "—"}</span>
        <div className="grow stack" style={{ gap: 6 }}>
          <div className="row between">
            <h3>{period.name}</h3>
            <span className="small muted num">{pct}%</span>
          </div>
          <Progress value={pct / 100} thin />
          <div className="tiny muted">{period.topics.length} mavzu · {solved}/{total} savol o'zlashtirilgan</div>
        </div>
      </button>
      {period.topics.map((t, i) => {
        const done = t.total > 0 && t.percent >= 100;
        const started = t.solved > 0;
        return (
          <button key={t.id} className="lesson-row" onClick={() => go(`/lesson?mode=topic&id=${t.id}`)}>
            <span className={`status ${done ? "done" : started ? "started" : ""}`}>{done ? "✓" : i + 1}</span>
            <span className="grow" style={{ minWidth: 0 }}>
              <span className="ellipsis" style={{ display: "block", fontWeight: 500 }}>{t.name}</span>
              <span className="tiny muted">{t.solved}/{t.total} savol</span>
            </span>
            <span className="pct">{t.percent}%</span>
          </button>
        );
      })}
    </section>
  );
}

export function HomePage() {
  const { home } = useStore();
  if (!home) return null;
  const { done, goal } = home.today;
  const goalDone = done >= goal;
  const firstName = home.user.name.split(" ")[0] || "";
  const now = new Date();
  const rec = home.recommendation;

  return (
    <div className="page stack">
      <div className="page-head rise">
        <div>
          <div className="eyebrow">{now.getDate()}-{MONTHS[now.getMonth()]}</div>
          <h1>{greeting()}{firstName ? `, ${firstName}` : ""}</h1>
        </div>
      </div>

      {/* Asosiy ko'rsatkichlar */}
      <div className="metrics rise">
        <div className="metric">
          <span className="label"><Flame size={14} /> Ketma-ket</span>
          <span className="value">{home.user.streak}<small>kun</small></span>
        </div>
        <div className="metric">
          <span className="label"><Star size={14} /> Bu hafta</span>
          <span className="value">{home.week.xp}<small>XP</small></span>
        </div>
        <div className="metric">
          <span className="label"><Target size={14} /> Bugun</span>
          <span className="value">{Math.min(done, goal)}<small>/ {goal}</small></span>
        </div>
      </div>

      {/* Kunlik mashq — sahifadagi asosiy harakat */}
      <button className="card hero tap stack" style={{ gap: 12 }} onClick={() => go("/lesson?mode=daily")}>
        <div className="row between">
          <div>
            <div className="eyebrow" style={{ color: "rgba(255,255,255,.7)" }}>Kunlik mashq</div>
            <h2 style={{ marginTop: 2 }}>{goalDone ? "Bugungi maqsad bajarildi" : `${goal} ta savol`}</h2>
          </div>
          <span className="icon-box on-hero"><Target size={22} /></span>
        </div>
        <Progress value={done / goal} onColor />
        <div className="row between small">
          <span className="muted">{goalDone ? "Qo'shimcha mashq ham foydali" : "Takrorlash vaqti kelganlar + yangi savollar"}</span>
          <span className="bold row" style={{ gap: 4 }}>{done > 0 && !goalDone ? "Davom etish" : "Boshlash"} <ChevronRight size={16} /></span>
        </div>
      </button>

      <div className="grid-2" style={{ gridTemplateColumns: "1fr 1fr" }}>
        <button className={`card tap stack ${home.due_count ? "" : "disabled"}`} style={{ gap: 10 }} onClick={() => go("/lesson?mode=review")}>
          <span className="icon-box accent"><Refresh size={20} /></span>
          <div>
            <div className="bold">Takrorlash</div>
            <div className="small muted">{home.due_count ? `${home.due_count} ta savol kutmoqda` : "Hozircha yo'q"}</div>
          </div>
        </button>
        <button className="card tap stack" style={{ gap: 10 }} onClick={() => go("/exam")}>
          <span className="icon-box"><Clipboard size={20} /></span>
          <div>
            <div className="bold">Sinov imtihoni</div>
            <div className="small muted">{home.exam ? `${home.exam.count} savol · ${home.exam.minutes} daq.` : "Tez orada"}</div>
          </div>
        </button>
      </div>

      {/* Tavsiya: zaif yoki yangi mavzu */}
      {rec && (
        <button className="card tap row callout" style={{ "--c": rec.kind === "weak" ? "var(--danger)" : "var(--primary)" } as React.CSSProperties}
          onClick={() => go(`/lesson?mode=topic&id=${rec.id}`)}>
          <div className="grow" style={{ minWidth: 0 }}>
            <div className="eyebrow">{rec.kind === "weak" ? "Mustahkamlash tavsiya etiladi" : "Keyingi mavzu"}</div>
            <div className="bold ellipsis" style={{ marginTop: 2 }}>{rec.name}</div>
            <div className="small muted">
              {rec.kind === "weak" ? `Aniqlik ${rec.accuracy}% — mavzuni qayta ishlang` : `${rec.total} ta savol`}
            </div>
          </div>
          <ChevronRight size={18} />
        </button>
      )}

      {/* Tarixda bugun */}
      {home.history_today.length > 0 && (
        <div className="card stack" style={{ gap: 10 }}>
          <div className="row" style={{ color: "var(--accent)" }}>
            <Calendar size={18} /><span className="eyebrow" style={{ color: "var(--accent)" }}>Tarixda bugun</span>
          </div>
          {home.history_today.map((e, i) => (
            <div key={i} className="row" style={{ alignItems: "flex-start", gap: 14 }}>
              {e.year && <span className="serif bold num" style={{ fontSize: 18, minWidth: 48, color: "var(--accent)" }}>{e.year}</span>}
              <div>
                <div className="bold">{e.title}</div>
                {e.text && <div className="small muted">{e.text}</div>}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Kurs dasturi */}
      <div className="section-title">
        <span>Kurs dasturi</span>
        <span className="tiny muted">o'zlashtirish {home.mastery}%</span>
      </div>
      {home.path.length === 0 && (
        <div className="card empty">
          <span className="empty-icon"><Clipboard size={24} /></span>
          <div className="muted small">Hozircha savollar qo'shilmagan. Admin panel orqali savollar yuklang.</div>
        </div>
      )}
      {home.path.map((p, i) => <Unit key={p.id} period={p} index={i} />)}

      <button className="btn white block" onClick={() => go("/lesson?mode=mixed")}>Aralash test</button>

      <button className="card tap row" onClick={() => go("/invite")}>
        <span className="icon-box"><Users size={20} /></span>
        <div className="grow">
          <div className="bold">Do'stlarni taklif qilish</div>
          <div className="small muted">Har bir faol do'st uchun bonus XP</div>
        </div>
        <ChevronRight size={18} />
      </button>
    </div>
  );
}
