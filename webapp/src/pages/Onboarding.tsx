import { useState } from "react";
import { Mascot } from "../components/Mascot";
import { toast } from "../components/ui";
import { api } from "../lib/api";
import { useStore } from "../lib/store";
import { haptic } from "../lib/telegram";
import { toCyrillic as toCyr, type Alphabet } from "../lib/translit";

const FEATURES: [string, string, string][] = [
  ["🔥", "Har kuni 10 ta savol", "Ketma-ket kunlarni uzmang"],
  ["🔁", "Xatolar ustida ishlash", "Xato savollar o'z vaqtida qaytadi"],
  ["🎯", "Sinov imtihoni", "Taymer, ball va daraja bilan"],
];

/** Birinchi kirishda: kutib olish va alifbo tanlash */
export function Onboarding() {
  const { reload } = useStore();
  const [choice, setChoice] = useState<Alphabet | null>(null);
  const [busy, setBusy] = useState(false);
  const L = (latn: string, cyrl: string) => (choice === "cyrl" ? cyrl : latn);

  async function start() {
    if (!choice) return;
    setBusy(true);
    try {
      await api("/me", { method: "PATCH", body: { alphabet: choice } });
      haptic.success();
      await reload();
    } catch (e) {
      toast((e as Error).message, "error");
      setBusy(false);
    }
  }

  return (
    <div className="page no-nav onboarding">
      <div className="center stack" style={{ alignItems: "center", gap: 6 }}>
        <div className="bubble pop">{L("Salom! Men Tarixchiman 👋", "Салом! Мен Тарихчиман 👋")}</div>
        <Mascot size={150} mood="happy" className="bob" />
        <h1 style={{ fontSize: 26 }}>{L("Tarixni o'yin kabi o'rganing", "Тарихни ўйин каби ўрганинг")}</h1>
        <p className="muted">{L("Milliy sertifikatga tayyorgarlik", "Миллий сертификатга тайёргарлик")}</p>
      </div>
      <div className="stack" style={{ marginTop: 20 }}>
        {FEATURES.map(([icon, title, sub]) => (
          <div key={title} className="row feature-line">
            <span className="feature-emoji">{icon}</span>
            <div><div className="bold">{L(title, toCyr(title))}</div><div className="small muted">{L(sub, toCyr(sub))}</div></div>
          </div>
        ))}
      </div>
      <div className="section-title" style={{ marginTop: 20 }}>{L("Alifboni tanlang", "Алифбони танланг")}</div>
      <div className="alphabet-pick">
        {([["latn", "Aa", "Lotin"], ["cyrl", "Аа", "Кирилл"]] as const).map(([v, big, label]) => (
          <button key={v} className={`pick ${choice === v ? "on" : ""}`} onClick={() => { haptic.select(); setChoice(v); }}>
            <span className="big">{big}</span>{label}
          </button>
        ))}
      </div>
      <div className="footer-bar"><div className="inner">
        <button className="btn block" disabled={!choice || busy} onClick={start}>{L("Boshlash", "Бошлаш")}</button>
      </div></div>
    </div>
  );
}
