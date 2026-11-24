import { useEffect, useState, type ReactNode } from "react";

export function Progress({ value, color, thin, onColor }: { value: number; color?: string; thin?: boolean; onColor?: boolean }) {
  const pct = Math.max(0, Math.min(100, value * 100));
  return (
    <div className={`progress ${thin ? "thin" : ""} ${onColor ? "on-color" : ""}`}>
      <i style={{ width: `${pct}%`, ...(color ? ({ "--c": color } as React.CSSProperties) : {}) }} />
    </div>
  );
}

/** Aylana progress (mavzu tugunlari va natijalar uchun) */
export function Ring({ value, size = 96, stroke = 8, color = "var(--primary)", children }: {
  value: number; size?: number; stroke?: number; color?: string; children?: ReactNode;
}) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  return (
    <div style={{ position: "relative", width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        <circle cx={size / 2} cy={size / 2} r={r} stroke="var(--surface-2)" strokeWidth={stroke} fill="none" />
        <circle cx={size / 2} cy={size / 2} r={r} stroke={color} strokeWidth={stroke} fill="none"
          strokeLinecap="round" strokeDasharray={c} strokeDashoffset={c * (1 - Math.max(0, Math.min(1, value)))}
          style={{ transition: "stroke-dashoffset .6s ease" }} />
      </svg>
      <div style={{ position: "absolute", inset: 0, display: "grid", placeItems: "center" }}>{children}</div>
    </div>
  );
}

export function Spinner() {
  return <div className="spinner" />;
}

export function Loading() {
  return <div className="loading-screen"><Spinner /></div>;
}

export function Sheet({ onClose, children }: { onClose: () => void; children: ReactNode }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div className="backdrop" onClick={onClose}>
      <div className="sheet" onClick={(e) => e.stopPropagation()}>{children}</div>
    </div>
  );
}

export function Switch({ on, onChange }: { on: boolean; onChange: (v: boolean) => void }) {
  return <button type="button" className={`switch ${on ? "on" : ""}`} onClick={() => onChange(!on)} aria-pressed={on} />;
}

export function Segmented<T extends string | number>({ value, options, onChange }: {
  value: T; options: { value: T; label: ReactNode }[]; onChange: (v: T) => void;
}) {
  return (
    <div className="segmented">
      {options.map((o) => (
        <button type="button" key={String(o.value)} className={o.value === value ? "on" : ""} onClick={() => onChange(o.value)}>
          {o.label}
        </button>
      ))}
    </div>
  );
}

// ---- Qisqa bildirishnomalar (toast) ----
type ToastMsg = { text: string; kind: "info" | "error" | "success"; id: number };
let pushToast: ((t: ToastMsg) => void) | null = null;
export function toast(text: string, kind: ToastMsg["kind"] = "info"): void {
  pushToast?.({ text, kind, id: Date.now() });
}
export function ToastHost() {
  const [msg, setMsg] = useState<ToastMsg | null>(null);
  useEffect(() => {
    pushToast = setMsg;
    return () => { pushToast = null; };
  }, []);
  useEffect(() => {
    if (!msg) return;
    const id = setTimeout(() => setMsg(null), 2800);
    return () => clearTimeout(id);
  }, [msg]);
  return msg ? <div key={msg.id} className={`toast ${msg.kind}`}>{msg.text}</div> : null;
}

export function Avatar({ name, size = "" }: { name: string; size?: "" | "lg" | "xl"; seed?: number }) {
  const letters = name.split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase() || "?";
  return <div className={`avatar ${size}`}>{letters}</div>;
}

/** Qiyinlik: uchta kichik ustun (oson / o'rta / qiyin) */
export function Stars({ n }: { n: number }) {
  const label = ["", "Oson", "O'rta", "Qiyin"][n] ?? "";
  return (
    <span className="chip" title={label} style={{ gap: 6 }}>
      <span style={{ display: "inline-flex", gap: 2, alignItems: "flex-end" }} aria-hidden>
        {[1, 2, 3].map((i) => (
          <span key={i} style={{ width: 3, height: 4 + i * 3, borderRadius: 1, background: i <= n ? "var(--text-2)" : "var(--border-strong)" }} />
        ))}
      </span>
      {label}
    </span>
  );
}

/** Foizga qarab rang: qizil < 40 ≤ oltin < 80 ≤ yashil */
export const levelColor = (p: number) => (p >= 80 ? "var(--success)" : p >= 40 ? "var(--accent)" : "var(--danger)");
