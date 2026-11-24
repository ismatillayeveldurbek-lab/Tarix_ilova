import { useRef, useState } from "react";
import { Download, Upload } from "../../components/Icons";
import { Spinner, toast } from "../../components/ui";
import { api, download } from "../../lib/api";
import type { ImportReport } from "./shared";

function UploadBox({ kind, title, columns, notes }: {
  kind: "questions" | "history"; title: string; columns: string[]; notes: string[];
}) {
  const input = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);
  const [busy, setBusy] = useState(false);
  const [report, setReport] = useState<(ImportReport & { file: string }) | null>(null);

  async function upload(file: File) {
    if (!/\.(xlsx|csv)$/i.test(file.name)) return toast("Faqat .xlsx yoki .csv fayl", "error");
    const form = new FormData();
    form.append("file", file);
    setBusy(true);
    setReport(null);
    try {
      const r = await api<ImportReport>(`/admin/import/${kind}`, { form });
      setReport({ ...r, file: file.name });
      toast(`${r.added} ta qo'shildi`, r.added ? "success" : "info");
    } catch (e) {
      toast((e as Error).message, "error");
    } finally {
      setBusy(false);
      if (input.current) input.current.value = "";
    }
  }

  return (
    <div className="card stack">
      <h2 style={{ fontSize: 20 }}>{title}</h2>
      <div className={`dropzone ${over ? "over" : ""}`}
        onClick={() => input.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setOver(true); }}
        onDragLeave={() => setOver(false)}
        onDrop={(e) => { e.preventDefault(); setOver(false); const f = e.dataTransfer.files[0]; if (f) void upload(f); }}>
        {busy ? <Spinner /> : <span style={{ color: "var(--success)" }}><Upload size={40} /></span>}
        <div className="bold">{busy ? "Yuklanmoqda..." : "Faylni shu yerga tashlang yoki bosing"}</div>
        <div className="small muted">.xlsx (Excel) yoki .csv · 10 MB gacha</div>
        <input ref={input} type="file" accept=".xlsx,.csv" hidden onChange={(e) => { const f = e.target.files?.[0]; if (f) void upload(f); }} />
      </div>
      {report && (
        <div className="stack" style={{ gap: 8 }}>
          <div className="bold">{report.file}</div>
          <div className="row" style={{ flexWrap: "wrap" }}>
            <span className="chip green">Qo'shildi: {report.added}</span>
            <span className="chip">Takroriy: {report.skipped_duplicates}</span>
            <span className={`chip ${report.errors.length ? "red" : ""}`}>Xato qatorlar: {report.errors.length}</span>
          </div>
          {report.errors.length > 0 && <ul className="err-list">{report.errors.map((e) => <li key={e}>{e}</li>)}</ul>}
        </div>
      )}
      <div>
        <div className="bold small" style={{ marginBottom: 6 }}>Ustunlar (1-qatorda):</div>
        <div className="row" style={{ flexWrap: "wrap", gap: 6 }}>{columns.map((c) => <code key={c} className="chip blue">{c}</code>)}</div>
        <ul className="small muted" style={{ paddingLeft: 18, marginBottom: 0 }}>{notes.map((n) => <li key={n}>{n}</li>)}</ul>
      </div>
      <div className="row" style={{ flexWrap: "wrap" }}>
        <button className="btn sm white" onClick={() => download(`/admin/template/${kind}.xlsx`, `${kind}_shablon.xlsx`).catch((e) => toast(e.message, "error"))}>
          <Download size={18} /> Excel shablon
        </button>
        <button className="btn sm white" onClick={() => download(`/admin/template/${kind}.csv`, `${kind}_shablon.csv`).catch((e) => toast(e.message, "error"))}>
          <Download size={18} /> CSV shablon
        </button>
      </div>
    </div>
  );
}

export function ImportPage() {
  return (
    <div className="stack">
      <h1>Import</h1>
      <p className="muted">Shablonni yuklab oling, to'ldiring va shu yerga yuklang. Matni bir xil yozuvlar qayta qo'shilmaydi, shuning uchun bitta faylni qayta yuklash xavfsiz.</p>
      <div className="card row" style={{ flexWrap: "wrap" }}>
        <div className="grow"><b>Zaxira nusxa:</b> <span className="muted">barcha ma'lumotni Excel'ga yuklab oling. Fayl import formatida — tahrirlab, qayta yuklash mumkin.</span></div>
        <button className="btn sm white" onClick={() => download("/admin/export/questions.xlsx", "savollar.xlsx").catch((e) => toast(e.message, "error"))}><Download size={18} /> Savollar</button>
        <button className="btn sm white" onClick={() => download("/admin/export/history.xlsx", "voqealar.xlsx").catch((e) => toast(e.message, "error"))}><Download size={18} /> Voqealar</button>
      </div>
      <div className="grid-2">
        <UploadBox kind="questions" title="Test savollari"
          columns={["savol", "a", "b", "c", "d", "togri", "izoh", "mavzu", "davr", "qiyinlik", "rasm"]}
          notes={[
            "togri — A, B, C yoki D",
            "qiyinlik — 1, 2, 3 yoki oson / o'rta / qiyin (bo'sh bo'lsa 1)",
            "rasm — ixtiyoriy, https:// havola (yoki keyin savolni tahrirlab rasm yuklang)",
            "Yangi davr va mavzular avtomatik yaratiladi",
          ]} />
        <UploadBox kind="history" title="Tarixda bugun"
          columns={["oy", "kun", "yil", "sarlavha", "matn"]}
          notes={["oy — 1–12, kun — 1–31", "yil ixtiyoriy", "Har kuni belgilangan vaqtda kanal va botga yuboriladi"]} />
      </div>
    </div>
  );
}
