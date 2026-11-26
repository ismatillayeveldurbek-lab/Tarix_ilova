import { useState } from "react";
import type { Question } from "../lib/types";
import { Stars } from "./ui";

type State = "idle" | "selected" | "correct" | "wrong";

/** Savol matni va variantlar. Dars ham, imtihon ham shundan foydalanadi. */
export function QuestionView({ q, selected, correct, locked, onSelect }: {
  q: Question;
  selected: string | null;
  correct?: string | null;
  locked?: boolean;
  onSelect: (key: string) => void;
}) {
  const stateOf = (key: string): State => {
    if (correct) {
      if (key === correct) return "correct";
      if (key === selected) return "wrong";
      return "idle";
    }
    return key === selected ? "selected" : "idle";
  };
  return (
    <div>
      <div className="row" style={{ flexWrap: "wrap", gap: 6 }}>
        {q.period && <span className="chip blue">{q.period}</span>}
        {q.topic && <span className="chip">{q.topic}</span>}
        <Stars n={q.difficulty} />
      </div>
      {q.image && <QuestionImage src={q.image} />}
      <div className="q-text">{q.text}</div>
      <div className="options">
        {q.options.map((o) => {
          const st = stateOf(o.key);
          return (
            <button key={o.key} className={`option ${st === "idle" ? "" : st}`} disabled={locked}
              onClick={() => onSelect(o.key)}>
              <span className="key">{o.key.toUpperCase()}</span>
              <span className="grow">{o.text}</span>
            </button>
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
      <button type="button" className="q-image" onClick={() => setZoom(true)}>
        <img src={src} alt="" loading="lazy" onError={() => setFailed(true)} />
      </button>
      {zoom && (
        <div className="zoom" onClick={() => setZoom(false)}>
          <img src={src} alt="" />
        </div>
      )}
    </>
  );
}
