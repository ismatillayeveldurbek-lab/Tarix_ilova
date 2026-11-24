import { useStore } from "../lib/store";
import { Flame, Star, Target } from "./Icons";

/** Yuqoridagi panel: ketma-ket kunlar, haftalik XP, kunlik maqsad */
export function TopBar() {
  const { home } = useStore();
  if (!home) return null;
  const { streak } = home.user;
  const activeToday = home.today.done > 0;
  return (
    <div className="topbar">
      <span className={`stat-pill orange ${activeToday ? "" : "off"}`} title="Ketma-ket kunlar">
        <Flame size={26} /> {streak}
      </span>
      <span className="stat-pill gold" title="Haftalik XP"><Star size={24} /> {home.week.xp}</span>
      <span className="stat-pill blue" title="Kunlik maqsad">
        <Target size={24} /> {Math.min(home.today.done, home.today.goal)}/{home.today.goal}
      </span>
    </div>
  );
}
