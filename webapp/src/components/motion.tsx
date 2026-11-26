// Harakat komponentlari: chiziladigan halqa, uchib chiqadigan "+XP", konfetti.
import { useEffect, useState, type ReactNode } from "react";
import { cx } from "./kit";

/** Aylana progress: ochilganda 0 dan qiymatgacha chiziladi */
export function ProgressRing({ value, size = 120, stroke = 10, tone = "var(--primary)", track = "var(--surface-2)", children, delay = 120 }: {
  value: number; size?: number; stroke?: number; tone?: string; track?: string; children?: ReactNode; delay?: number;
}) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const [shown, setShown] = useState(0);
  useEffect(() => {
    const id = setTimeout(() => setShown(Math.max(0, Math.min(1, value))), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} stroke={track} strokeWidth={stroke} fill="none" />
        <circle cx={size / 2} cy={size / 2} r={r} stroke={tone} strokeWidth={stroke} fill="none" strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={c * (1 - shown)}
          style={{ transition: "stroke-dashoffset 1.1s cubic-bezier(.2,.8,.2,1)" }} />
      </svg>
      <div className="absolute inset-0 grid place-items-center">{children}</div>
    </div>
  );
}

/** "+10 XP" — bir marta yuqoriga uchib, so‘nadi */
export function FloatUp({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <span className={cx("pointer-events-none absolute animate-float-up whitespace-nowrap text-[17px] font-extrabold", className)}>
      {children}
    </span>
  );
}

const CONFETTI_COLORS = ["var(--c-sana)", "var(--c-shaxs)", "var(--c-atama)", "var(--c-joy)", "var(--accent)", "var(--primary)"];

/** Konfetti portlashi (natija ekranlarida, yaxshi natijada) */
export function Confetti({ pieces = 36 }: { pieces?: number }) {
  const [items] = useState(() => Array.from({ length: pieces }, (_, i) => {
    const angle = (Math.PI * 2 * i) / pieces + Math.random() * 0.4;
    const dist = 90 + Math.random() * 120;
    return {
      dx: Math.cos(angle) * dist, dy: Math.sin(angle) * dist * 0.8 + 60 + Math.random() * 80,
      rot: (Math.random() - 0.5) * 720, color: CONFETTI_COLORS[i % CONFETTI_COLORS.length],
      w: 6 + Math.random() * 5, h: 9 + Math.random() * 7, delay: Math.random() * 120,
    };
  }));
  return (
    <div aria-hidden className="pointer-events-none absolute left-1/2 top-1/2 h-0 w-0">
      {items.map((p, i) => (
        <span key={i} className="absolute animate-confetti rounded-[2px]"
          style={{
            width: p.w, height: p.h, background: p.color, animationDelay: `${p.delay}ms`,
            ["--dx" as string]: `${p.dx}px`, ["--dy" as string]: `${p.dy}px`, ["--rot" as string]: `${p.rot}deg`,
          }} />
      ))}
    </div>
  );
}
