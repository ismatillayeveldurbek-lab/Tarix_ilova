import { useCallback, useEffect, useRef, useState } from "react";
import { ChevronLeft, ChevronRight, Upload } from "../../components/Icons";
import { Loading, Sheet, Spinner, toast } from "../../components/ui";
import { api } from "../../lib/api";

type Fact = {
  id: string; tur: string; nom: string; matn: string; sana_matn: string; yil_boshi: number | null; yil_oxiri: number | null;
  asr: string; davr: string; hudud: string; sinf: number; book_id: string; source: string; mavzu_nomi: string;
  iqtibos: string; shaxs_faoliyati: string; shaxs_ishoralar: string[]; urush_tomonlari: string[]; golib: string;
  natija: string; joy_turi: string; joy_hozirgi: string; asar_muallifi: string; ishonch: string; izoh: string;
  flags: string[]; hidden_import: boolean; hidden_admin: boolean; visible: boolean;
};
type Summary = {
  total: number; visible: number; hidden_admin: number; by_type: Record<string, number>; by_davr: Record<string, number>;
  flags: Record<string, number>; books: { id: string; title: string; count: number }[];
};
type Page = { total: number; page: number; size: number; items: Fact[] };
type ImportReport = { total: number; added: number; updated: number; unchanged: number; hidden: number; missing_in_csv: number; flags: Record<string, number>; errors: string[] };

export const TYPES: Record<string, string> = { sana: "Sana", shaxs: "Shaxs", atama: "Atama", joy: "Joy", urush: "Urush", asar: "Asar" };
export const FLAG_LABELS: Record<string, string> = {
  ishonch_past: "Ishonch past", manba_yoq: "Manba yo'q", tur_nomalum: "Turi noma'lum", matn_yoq: "Matn yo'q",
  yil_yoq: "Aniq yil yo'q", yil_xato: "Yil xato", yil_asr_mos_emas: "Yil va asr mos emas",
  atama_ozini_tushuntiradi: "Ta'rifda atamaning o'zi", kontekstsiz: "Kontekstsiz gap",
  ishoralar_kam: "Ishoralar kam", csvda_yoq: "CSV'da yo'q",
};
const DAVRLAR = ["Qadimgi", "O‘rta asrlar", "Yangi", "Eng yangi"];
const HUDUDLAR = ["Jahon", "O‘zbekiston va Markaziy Osiyo"];

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  if (value === "" || value === null || value === undefined || (Array.isArray(value) && !value.length)) return null;
  return (
    <div className="row" style={{ alignItems: "flex-start", gap: 12 }}>
      <span className="small muted" style={{ minWidth: 120 }}>{label}</span>
      <span className="small grow">{value}</span>
    </div>
  );
}

function FactSheet({ fact, onClose, onChange }: { fact: Fact; onClose: () => void; onChange: (f: Fact) => void }) {
  const [busy, setBusy] = useState(false);
  async function toggle() {
    setBusy(true);
    try {
      onChange(await api<Fact>(`/admin/facts/${fact.id}`, { method: "PATCH", body: { hidden_admin: !fact.hidden_admin } }));
      toast(fact.hidden_admin ? "Fakt yana ko'rsatiladi" : "Fakt yashirildi", "success");
    } catch (e) {
      toast((e as Error).message, "error");
    } finally {
      setBusy(false);
    }
  }
  const year = fact.yil_boshi !== null ? `${fact.yil_boshi}${fact.yil_oxiri !== null ? ` … ${fact.yil_oxiri}` : ""}` : "";
  return (
    <Sheet onClose={onClose}>
      <div className="stack">
        <div className="row between">
          <span className="chip">{fact.id}</span>
          <span className={`chip ${fact.visible ? "green" : "red"}`}>{fact.visible ? "Ko'rinadi" : "Yashirin"}</span>
        </div>
        <div>
          <div className="eyebrow">{TYPES[fact.tur] ?? fact.tur} · {fact.davr} · {fact.hudud}</div>
          <h2 style={{ marginTop: 4 }}>{fact.nom}</h2>
        </div>
        <p>{fact.matn}</p>
        <div className="card" style={{ background: "var(--surface-2)", boxShadow: "none" }}>
          <div className="eyebrow">Darslikdan iqtibos</div>
          <div className="small" style={{ marginTop: 4, fontStyle: "italic" }}>«{fact.iqtibos}»</div>
          <div className="tiny muted" style={{ marginTop: 6 }}>{fact.source}{fact.mavzu_nomi ? ` · ${fact.mavzu_nomi}` : ""}</div>
        </div>
        <div className="stack" style={{ gap: 8 }}>
          <Field label="Sana" value={fact.sana_matn} />
          <Field label="Yil (son)" value={year} />
          <Field label="Asr" value={fact.asr} />
          <Field label="Faoliyati" value={fact.shaxs_faoliyati} />
          <Field label="Ishoralar" value={fact.shaxs_ishoralar.length ? <ol style={{ margin: 0, paddingLeft: 18 }}>{fact.shaxs_ishoralar.map((x) => <li key={x}>{x}</li>)}</ol> : ""} />
          <Field label="Tomonlar" value={fact.urush_tomonlari.join(" — ")} />
          <Field label="G'olib" value={fact.golib} />
          <Field label="Natija" value={fact.natija} />
          <Field label="Joy turi" value={fact.joy_turi} />
          <Field label="Hozirgi joy" value={fact.joy_hozirgi} />
          <Field label="Muallif" value={fact.asar_muallifi} />
          <Field label="Ishonch" value={fact.ishonch} />
        </div>
        {fact.flags.length > 0 && (
          <div className="row" style={{ flexWrap: "wrap", gap: 6 }}>
            {fact.flags.map((f) => <span key={f} className="chip gold">{FLAG_LABELS[f] ?? f}</span>)}
          </div>
        )}
        {fact.izoh && (
          <div className="card callout" style={{ "--c": "var(--accent)", boxShadow: "none" } as React.CSSProperties}>
            <div className="eyebrow">Metodist izohi (o'quvchiga ko'rinmaydi)</div>
            <div className="small" style={{ marginTop: 4 }}>{fact.izoh}</div>
          </div>
        )}
        {fact.hidden_import && <div className="small muted">Import tekshiruvi bu faktni yashirgan (masalan, ishonch past). Uni CSV'da tuzating.</div>}
        <div className="row">
          <button className="btn white grow" onClick={onClose}>Yopish</button>
          <button className={`btn grow ${fact.hidden_admin ? "" : "red"}`} disabled={busy} onClick={toggle}>
            {fact.hidden_admin ? "Yana ko'rsatish" : "Yashirish"}
          </button>
        </div>
      </div>
    </Sheet>
  );
}

function ImportBox({ onDone }: { onDone: () => void }) {
  const input = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportReport | null>(null);
  const [busy, setBusy] = useState(false);

  async function send(f: File, dryRun: boolean) {
    const form = new FormData();
    form.append("file", f);
    setBusy(true);
    try {
      const r = await api<ImportReport>(`/admin/import/facts${dryRun ? "?dry_run=true" : ""}`, { form });
      if (dryRun) setPreview(r);
      else {
        toast(`Import tugadi: +${r.added}, yangilandi ${r.updated}`, "success");
        setPreview(null);
        setFile(null);
        onDone();
      }
    } catch (e) {
      toast((e as Error).message, "error");
    } finally {
      setBusy(false);
      if (input.current) input.current.value = "";
    }
  }

  return (
    <div className="card stack">
      <div className="row between">
        <div>
          <div className="bold">Faktlar bazasini yangilash</div>
          <div className="small muted">CSV (UTF-8). Avval tekshiriladi, so'ng tasdiqlaysiz. Faktlar ID bo'yicha yangilanadi.</div>
        </div>
        <button className="btn sm white" disabled={busy} onClick={() => input.current?.click()}>
          {busy ? <Spinner /> : <Upload size={16} />} CSV tanlash
        </button>
        <input ref={input} type="file" accept=".csv" hidden onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) { setFile(f); void send(f, true); }
        }} />
      </div>
      {preview && file && (
        <div className="stack" style={{ gap: 8 }}>
          <div className="row" style={{ flexWrap: "wrap", gap: 6 }}>
            <span className="chip">{file.name}: {preview.total} qator</span>
            <span className="chip green">Yangi: {preview.added}</span>
            <span className="chip blue">O'zgargan: {preview.updated}</span>
            <span className="chip">O'zgarmagan: {preview.unchanged}</span>
            <span className="chip red">Yashiriladi: {preview.hidden}</span>
            {preview.missing_in_csv > 0 && <span className="chip gold">CSV'da yo'q: {preview.missing_in_csv}</span>}
          </div>
          {preview.errors.length > 0 && <ul className="err-list">{preview.errors.slice(0, 20).map((e) => <li key={e}>{e}</li>)}</ul>}
          <div className="row">
            <button className="btn white grow" onClick={() => { setPreview(null); setFile(null); }}>Bekor qilish</button>
            <button className="btn grow" disabled={busy} onClick={() => send(file, false)}>Importni tasdiqlash</button>
          </div>
        </div>
      )}
    </div>
  );
}

export function FactsPage() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [data, setData] = useState<Page | null>(null);
  const [f, setF] = useState({ q: "", tur: "", davr: "", hudud: "", book_id: "", flag: "", hidden: "" });
  const [page, setPage] = useState(1);
  const [open, setOpen] = useState<Fact | null>(null);

  const loadSummary = useCallback(() => api<Summary>("/admin/facts/summary").then(setSummary).catch((e) => toast(e.message, "error")), []);
  const load = useCallback(async () => {
    const p = new URLSearchParams({ page: String(page), size: "30" });
    Object.entries(f).forEach(([k, v]) => v && p.set(k, v));
    try {
      setData(await api<Page>(`/admin/facts?${p}`));
    } catch (e) {
      toast((e as Error).message, "error");
    }
  }, [f, page]);
  useEffect(() => { void loadSummary(); }, [loadSummary]);
  useEffect(() => {
    const id = setTimeout(load, 250);
    return () => clearTimeout(id);
  }, [load]);

  const set = (k: keyof typeof f) => (v: string) => { setF({ ...f, [k]: v }); setPage(1); };
  const pages = data ? Math.max(1, Math.ceil(data.total / data.size)) : 1;

  return (
    <div className="stack">
      <div>
        <h1>Faktlar bazasi</h1>
        <p className="muted small">Kartochka, test va o'yinlar shu faktlardan tuziladi. Har faktda darslik manbasi bor.</p>
      </div>

      {summary && (
        <div className="stat-grid">
          <div className="stat-card"><div className="v">{summary.total}</div><div className="l">Jami faktlar</div></div>
          <div className="stat-card"><div className="v">{summary.visible}</div><div className="l">O'quvchiga ko'rinadi</div></div>
          {Object.entries(summary.by_type).map(([t, n]) => (
            <div key={t} className="stat-card"><div className="v">{n}</div><div className="l">{TYPES[t] ?? t}</div></div>
          ))}
        </div>
      )}
      {summary && Object.keys(summary.flags).length > 0 && (
        <div className="card stack" style={{ gap: 8 }}>
          <div className="bold">Tekshiruv belgilari</div>
          <div className="row" style={{ flexWrap: "wrap", gap: 6 }}>
            {Object.entries(summary.flags).map(([k, n]) => (
              <button key={k} className={`chip ${f.flag === k ? "blue" : ""}`} style={{ cursor: "pointer" }} onClick={() => set("flag")(f.flag === k ? "" : k)}>
                {FLAG_LABELS[k] ?? k}: {n}
              </button>
            ))}
          </div>
          <div className="tiny muted">"Ishonch past" — o'quvchiga ko'rsatilmaydi. "Aniq yil yo'q" — kartochkada bor, yillar o'yinida yo'q.</div>
        </div>
      )}

      <ImportBox onDone={() => { void loadSummary(); void load(); }} />

      <div className="toolbar">
        <input className="input" placeholder="Qidirish (nom, matn, ID)..." value={f.q} onChange={(e) => set("q")(e.target.value)} />
        <select className="select" value={f.tur} onChange={(e) => set("tur")(e.target.value)}>
          <option value="">Barcha turlar</option>
          {Object.entries(TYPES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <select className="select" value={f.davr} onChange={(e) => set("davr")(e.target.value)}>
          <option value="">Barcha davrlar</option>
          {DAVRLAR.map((d) => <option key={d}>{d}</option>)}
        </select>
        <select className="select" value={f.hudud} onChange={(e) => set("hudud")(e.target.value)}>
          <option value="">Jahon va O‘zbekiston</option>
          {HUDUDLAR.map((d) => <option key={d}>{d}</option>)}
        </select>
        <select className="select" value={f.book_id} onChange={(e) => set("book_id")(e.target.value)}>
          <option value="">Barcha darsliklar</option>
          {summary?.books.map((b) => <option key={b.id} value={b.id}>{b.title} ({b.count})</option>)}
        </select>
        <select className="select" value={f.hidden} onChange={(e) => set("hidden")(e.target.value)}>
          <option value="">Hammasi</option>
          <option value="false">Ko'rinadiganlar</option>
          <option value="true">Yashirinlar</option>
        </select>
      </div>

      {!data ? <Loading /> : (
        <div className="stack" style={{ gap: 8 }}>
          <div className="small muted">{data.total} ta fakt topildi</div>
          {data.items.map((x) => (
            <button key={x.id} className={`q-item ${x.visible ? "" : "inactive"}`} onClick={() => setOpen(x)}>
              <span className="q-id" style={{ minWidth: 86 }}>{x.id}</span>
              <div className="grow stack" style={{ gap: 4 }}>
                <div className="row" style={{ gap: 8 }}>
                  <span className="chip">{TYPES[x.tur] ?? x.tur}</span>
                  <span className="bold">{x.nom}</span>
                  {x.sana_matn && <span className="small muted">{x.sana_matn}</span>}
                </div>
                <div className="small" style={{ color: "var(--text-2)" }}>{x.matn}</div>
                <div className="row" style={{ flexWrap: "wrap", gap: 6 }}>
                  <span className="tiny muted">{x.source}</span>
                  {x.flags.map((fl) => <span key={fl} className="chip gold">{FLAG_LABELS[fl] ?? fl}</span>)}
                  {x.hidden_admin && <span className="chip red">Admin yashirgan</span>}
                </div>
              </div>
            </button>
          ))}
          {pages > 1 && (
            <div className="row" style={{ justifyContent: "center" }}>
              <button className="btn sm white" disabled={page <= 1} onClick={() => setPage(page - 1)}><ChevronLeft size={16} /></button>
              <span className="small bold num">{page} / {pages}</span>
              <button className="btn sm white" disabled={page >= pages} onClick={() => setPage(page + 1)}><ChevronRight size={16} /></button>
            </div>
          )}
        </div>
      )}
      {open && (
        <FactSheet fact={open} onClose={() => setOpen(null)}
          onChange={(nf) => { setOpen(nf); setData((d) => d && { ...d, items: d.items.map((i) => (i.id === nf.id ? nf : i)) }); void loadSummary(); }} />
      )}
    </div>
  );
}
