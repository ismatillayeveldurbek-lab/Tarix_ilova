import { useState } from "react";
import type { Question } from "../lib/types";
import { Check, Cross } from "./Icons";
import { Pill, cx } from "./kit";

type State = "idle" | "selected" | "correct" | "wrong" | "dim";

const OPTION: Record<State, string> = {
  idle: "border-line bg-surface hover:border-line-strong active:scale-[.99]",
  selected: "border-peri bg-peri-soft shadow-[0_0_0_3px_color-mix(in_srgb,var(--primary)_14%,transparent)]",
  correct: "border-success bg-success-soft animate-glow",
  wrong: "border-danger bg-danger-soft animate-shake",
  dim: "border-line bg-surface opacity-45",
};
const KEY: Record<State, string> = {
  idle: "bg-surface-2 text-muted",
  selected: "bg-cta text-on-cta",
  correct: "bg-success text-on-success animate-pop",
  wrong: "bg-danger text-white animate-pop",
  dim: "bg-surface-2 text-faint",
};

/** Qiyinlik: uchta kichik ustun */
export function Difficulty({ n }: { n: number }) {
  const label = ["", "Oson", "O‘rta", "Qiyin"][n] ?? "";
  return (
    <Pill>
      <span className="inline-flex items-end gap-[2px]" aria-hidden>
        {[1, 2, 3].map((i) => (
          <span key={i} className={cx("w-[3px] rounded-[1px]", i <= n ? "bg-ink-2" : "bg-line-strong")} style={{ height: 4 + i * 3 }} />
        ))}
      </span>
      {label}
    </Pill>
  );
}

/** Savol matni va variantlar. Dars ham, imtihon ham shundan foydalanadi. */
export function QuestionView({ q, selected, correct, locked, onSelect, meta = true }: {
  q: Question;
  selected: string | null;
  correct?: string | null;
  locked?: boolean;
  onSelect: (key: string) => void;
  meta?: boolean;
}) {
  const stateOf = (key: string): State => {
    if (correct) {
      if (key === correct) return "correct";
      if (key === selected) return "wrong";
      return "dim";
    }
    return key === selected ? "selected" : "idle";
  };
  return (
    <div>
      {meta && (
        <div className="flex flex-wrap items-center gap-1.5">
          {q.period && <Pill className="bg-peri-soft text-peri">{q.period}</Pill>}
          {q.topic && <Pill className="max-w-full truncate bg-surface-2 text-muted">{q.topic}</Pill>}
          <Difficulty n={q.difficulty} />
        </div>
      )}
      {q.image && <QuestionImage src={q.image} />}
      <p className="mt-4 font-reading text-[20px] leading-[1.45] text-ink">{q.text}</p>
      <div className="stagger mt-5 space-y-2.5">
        {q.options.map((o) => {
          const st = stateOf(o.key);
          return (
            <div key={o.key}><button type="button" disabled={locked} onClick={() => onSelect(o.key)}
              className={cx("relative flex w-full items-center gap-3 rounded-[18px] border-2 px-3.5 py-3 text-left transition duration-200", OPTION[st])}>
              <span className={cx("relative grid h-8 w-8 shrink-0 place-items-center rounded-full text-[14px] font-bold transition-colors", KEY[st])}>
                {st === "correct" ? <Check size={17} /> : st === "wrong" ? <Cross size={17} /> : o.key.toUpperCase()}
                {st === "correct" && <span className="absolute inset-0 animate-okring rounded-full border-2 border-success" />}
              </span>
              <span className="min-w-0 flex-1 text-[16px] font-medium leading-snug text-ink">{o.text}</span>
            </button></div>
          );
        })}
      </div>
    </div>
  );
}

/** Savol rasmi: bosilsa to‘liq ekranda ochiladi */
function QuestionImage({ src }: { src: string }) {
  const [zoom, setZoom] = useState(false);
  const [failed, setFailed] = useState(false);
  if (failed) return null;
  return (
    <>
      <button type="button" onClick={() => setZoom(true)}
        className="mt-4 block w-full overflow-hidden rounded-2xl border border-line bg-surface-2">
        <img src={src} alt="" loading="lazy" onError={() => setFailed(true)} className="mx-auto max-h-[260px] w-auto object-contain" />
      </button>
      {zoom && (
        <div className="fixed inset-0 z-50 grid animate-fade place-items-center bg-black/80 p-4" onClick={() => setZoom(false)}>
          <img src={src} alt="" className="max-h-full max-w-full animate-pop rounded-xl" />
        </div>
      )}
    </>
  );
}
