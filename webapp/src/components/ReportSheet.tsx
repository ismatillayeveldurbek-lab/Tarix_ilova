import { useState } from "react";
import { api } from "../lib/api";
import { useStore } from "../lib/store";
import { Flag } from "./Icons";
import { Sheet, toast } from "./ui";

/** "Savolda xato bor" oynasi */
export function ReportSheet({ questionId, onClose }: { questionId: number; onClose: () => void }) {
  const { t } = useStore();
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const quick = ["To'g'ri javob noto'g'ri belgilangan", "Savol matnida xato bor", "Izoh noto'g'ri", "Variantlarda xato bor"];

  async function send() {
    setBusy(true);
    try {
      await api("/reports", { body: { question_id: questionId, comment: text.trim() } });
      toast(t("Rahmat! Xabaringiz adminlarga yuborildi"), "success");
      onClose();
    } catch (e) {
      toast((e as Error).message, "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Sheet onClose={onClose}>
      <div className="stack">
        <div className="row" style={{ color: "var(--red)" }}><Flag /><h2 style={{ fontSize: 20 }}>{t("Xato haqida xabar berish")}</h2></div>
        <div className="row" style={{ flexWrap: "wrap", gap: 6 }}>
          {quick.map((q) => (
            <button key={q} type="button" className="chip" style={{ border: 0, padding: "7px 12px" }} onClick={() => setText(q)}>{t(q)}</button>
          ))}
        </div>
        <textarea className="textarea" placeholder={t("Xatoni qisqacha yozing...")} value={text} onChange={(e) => setText(e.target.value)} maxLength={2000} />
        <button className="btn red block" disabled={!text.trim() || busy} onClick={send}>{t("Yuborish")}</button>
      </div>
    </Sheet>
  );
}
