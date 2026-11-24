import { useStore } from "../lib/store";
import { Check } from "./Icons";

const DAYS = ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"];

export function WeekStrip() {
  const { home, t } = useStore();
  if (!home) return null;
  const days = home.week.days;
  return (
    <div className="week">
      {days.map((d, i) => (
        <div key={d.date} className={`day ${d.active ? "active" : ""} ${i === days.length - 1 ? "today" : ""}`}>
          <span>{t(DAYS[d.weekday])}</span>
          <span className="dot">{d.active ? <Check size={18} /> : null}</span>
        </div>
      ))}
    </div>
  );
}
