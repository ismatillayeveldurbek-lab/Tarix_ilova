// Mezon uslubidagi asosiy UI qismlar (Tailwind). Yangi sahifalar shulardan quriladi.
import type { ReactNode } from "react";
import { ChevronRight } from "./Icons";

export const cx = (...c: (string | false | null | undefined)[]) => c.filter(Boolean).join(" ");

/** 3840 -> "3 840" */
export const fmt = (n: number) => n.toLocaleString("ru-RU").replace(/ /g, " ");

/** Oq, yumaloq karta. onClick bo‘lsa — bosiladigan */
export function Card({ children, className, onClick }: { children: ReactNode; className?: string; onClick?: () => void }) {
  const base = "block w-full text-left bg-surface border border-line rounded-card shadow-soft";
  if (onClick) {
    return (
      <button type="button" onClick={onClick}
        className={cx(base, "transition duration-200 hover:-translate-y-0.5 hover:border-line-strong hover:shadow-lift active:translate-y-0 active:scale-[.985]", className)}>
        {children}
      </button>
    );
  }
  return <div className={cx(base, className)}>{children}</div>;
}

/** To‘q ko‘k "hero" karta (asosiy harakat) */
export function HeroCard({ children, className, onClick }: { children: ReactNode; className?: string; onClick?: () => void }) {
  const cls = cx(
    "block w-full text-left rounded-card p-5 text-white shadow-lift",
    "bg-[radial-gradient(120%_90%_at_100%_0%,#2b4c8c_0%,transparent_55%),linear-gradient(135deg,#16295a_0%,#0f1b33_70%)]",
    onClick && "transition active:scale-[.99]", className,
  );
  return onClick ? <button type="button" onClick={onClick} className={cls}>{children}</button> : <div className={cls}>{children}</div>;
}

export function SectionTitle({ children, right }: { children: ReactNode; right?: ReactNode }) {
  return (
    <div className="flex items-end justify-between px-1 pt-3">
      <h2 className="text-[19px] font-bold tracking-tight text-ink">{children}</h2>
      {right && <div className="text-[13px] font-semibold text-muted">{right}</div>}
    </div>
  );
}

/** Rangli kvadrat ikonka. tone: bo‘lim rangi (sana, shaxs, ...) yoki holat */
const TONES: Record<string, string> = {
  sana: "bg-sana-soft text-sana", shaxs: "bg-shaxs-soft text-shaxs", atama: "bg-atama-soft text-atama",
  joy: "bg-joy-soft text-joy", urush: "bg-urush-soft text-urush", asar: "bg-asar-soft text-asar",
  peri: "bg-peri-soft text-peri", peach: "bg-peach-soft text-peach", success: "bg-success-soft text-success",
  danger: "bg-danger-soft text-danger", muted: "bg-surface-2 text-muted",
};
export function IconTile({ children, tone = "peri", size = 44 }: { children: ReactNode; tone?: string; size?: number }) {
  return (
    <span className={cx("grid shrink-0 place-items-center rounded-[14px]", TONES[tone] ?? TONES.peri)} style={{ width: size, height: size }}>
      {children}
    </span>
  );
}

/** Ro‘yxat qatori: ikonka, sarlavha, izoh, o‘ng tomonda qiymat yoki strelka */
export function ListRow({ icon, title, subtitle, right, onClick, disabled }: {
  icon?: ReactNode; title: ReactNode; subtitle?: ReactNode; right?: ReactNode; onClick?: () => void; disabled?: boolean;
}) {
  return (
    <button type="button" onClick={disabled ? undefined : onClick} disabled={disabled && !onClick}
      className={cx("flex w-full items-center gap-3 px-4 py-3.5 text-left transition",
        onClick && !disabled ? "hover:bg-surface-2/60 active:bg-surface-2" : "cursor-default",
        disabled && "opacity-55")}>
      {icon}
      <span className="min-w-0 flex-1">
        <span className="block truncate text-[15.5px] font-semibold text-ink">{title}</span>
        {subtitle && <span className="block truncate text-[13px] text-muted">{subtitle}</span>}
      </span>
      {right ?? (onClick && !disabled ? <ChevronRight size={18} className="text-faint" /> : null)}
    </button>
  );
}

export function Bar({ value, className, tone = "bg-cta" }: { value: number; className?: string; tone?: string }) {
  return (
    <div className={cx("h-2 overflow-hidden rounded-full bg-surface-2", className)}>
      <div className={cx("h-full rounded-full transition-[width] duration-700 ease-out-soft", tone)} style={{ width: `${Math.max(0, Math.min(1, value)) * 100}%` }} />
    </div>
  );
}

export function Pill({ children, className }: { children: ReactNode; className?: string }) {
  return <span className={cx("inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2.5 py-1 text-[12px] font-semibold", className ?? "bg-surface-2 text-muted")}>{children}</span>;
}

export function Initials({ name, size = 44 }: { name: string; size?: number }) {
  const letters = name.split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase() || "?";
  return (
    <span className="grid shrink-0 place-items-center rounded-full bg-peri-soft font-bold text-peri ring-2 ring-surface"
      style={{ width: size, height: size, fontSize: size * 0.38 }}>{letters}</span>
  );
}

/** Sahifa konteyneri: Telegram safe-area va pastki menyu uchun joy */
export function Screen({ children, nav = true }: { children: ReactNode; nav?: boolean }) {
  return (
    <div className={cx("stagger mx-auto max-w-[560px] space-y-4 px-4 pt-[calc(var(--safe-top)+16px)]",
      nav ? "pb-[calc(var(--safe-bottom)+96px)]" : "pb-[calc(var(--safe-bottom)+32px)]")}>
      {children}
    </div>
  );
}
