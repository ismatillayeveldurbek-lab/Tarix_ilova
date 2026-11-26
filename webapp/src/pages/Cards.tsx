import { useEffect, useState } from "react";
import { Book, Check, Close, Refresh } from "../components/Icons";
import { Bar, Pill, cx } from "../components/kit";
import { Loading, toast } from "../components/ui";
import { api } from "../lib/api";
import { navigate } from "../lib/router";
import { useStore } from "../lib/store";
import { confirmDialog, haptic } from "../lib/telegram";

type Front = { fact_id: string; tur: string; label: string; prompt: string; body: string; hints: string[]; davr: string; sinf: number };
type Back = { fact_id: string; answer: string; title: string; text: string; extra: string[]; sana: string; source: string; mavzu: string; iqtibos: string };
type Queue = { cards: Front[]; due: number; new_left: number };

const TONE: Record<string, string> = {
  sana: "bg-sana-soft text-sana", shaxs: "bg-shaxs-soft text-shaxs", atama: "bg-atama-soft text-atama",
  joy: "bg-joy-soft text-joy", urush: "bg-urush-soft text-urush", asar: "bg-asar-soft text-asar",
};

/** Kunlik takrorlash: karta → "Javobni ko'rish" → "Bildim / Bilmadim" */
export function CardsPage({ tur, davr }: { tur: string; davr: string }) {
  const { reload } = useStore();
  const [queue, setQueue] = useState<Queue | null>(null);
  const [idx, setIdx] = useState(0);
  const [back, setBack] = useState<Back | null>(null);
  const [busy, setBusy] = useState(false);
  const [showQuote, setShowQuote] = useState(false);
  const [stats, setStats] = useState({ knew: 0, forgot: 0 });
  const [round, setRound] = useState(0);

  useEffect(() => {
    const p = new URLSearchParams({ limit: "20" });
    if (tur) p.set("tur", tur);
    if (davr) p.set("davr", davr);
    setQueue(null);
    api<Queue>(`/v1/cards?${p}`).then((q) => { setQueue(q); setIdx(0); setBack(null); })
      .catch((e) => toast(e.message, "error"));
  }, [tur, davr, round]);

  useEffect(() => {
    document.body.classList.add("hide-nav");
    return () => document.body.classList.remove("hide-nav");
  }, []);

  if (!queue) return <Loading />;
  const total = queue.cards.length;
  const card = queue.cards[idx];
  const finished = idx >= total;

  async function reveal() {
    if (!card || busy) return;
    setBusy(true);
    try {
      setBack(await api<Back>(`/v1/cards/${card.fact_id}/reveal`, { method: "POST" }));
      haptic.tap();
    } catch (e) {
      toast((e as Error).message, "error");
    } finally {
      setBusy(false);
    }
  }

  async function grade(knew: boolean) {
    if (!card || busy) return;
    setBusy(true);
    try {
      await api(`/v1/cards/${card.fact_id}/grade`, { body: { knew } });
      if (knew) haptic.success(); else haptic.error();
      setStats((s) => ({ knew: s.knew + (knew ? 1 : 0), forgot: s.forgot + (knew ? 0 : 1) }));
      setBack(null);
      setShowQuote(false);
      setIdx((i) => i + 1);
      window.scrollTo(0, 0);
    } catch (e) {
      toast((e as Error).message, "error");
    } finally {
      setBusy(false);
    }
  }

  async function quit() {
    if (idx === 0 || finished || (await confirmDialog("Takrorlashni to‘xtatasizmi? Natijalar saqlangan."))) {
      void reload();
      navigate("/", true);
    }
  }

  const wrap = "mx-auto max-w-[560px] px-4";

  if (total === 0 || finished) {
    const doneSome = stats.knew + stats.forgot > 0;
    return (
      <div className={cx(wrap, "flex min-h-screen flex-col items-center justify-center gap-4 pb-[calc(var(--safe-bottom)+24px)] pt-[calc(var(--safe-top)+24px)] text-center")}>
        <span className={cx("grid h-16 w-16 place-items-center rounded-[20px]", doneSome ? "bg-success-soft text-success" : "bg-peri-soft text-peri")}>
          {doneSome ? <Check size={30} /> : <Refresh size={28} />}
        </span>
        <h1 className="text-[24px] font-extrabold tracking-tight text-ink">
          {doneSome ? "Takrorlash yakunlandi" : "Hozircha karta yo‘q"}
        </h1>
        {doneSome ? (
          <p className="text-[15px] text-muted">
            Bu safar: <b className="text-success">{stats.knew} bildim</b>, <b className="text-danger">{stats.forgot} takrorlashga</b>.
            <br />Bilmagan kartalaringiz 10 daqiqadan keyin qaytadi.
          </p>
        ) : (
          <p className="text-[15px] text-muted">
            {queue.new_left === 0 ? "Bugungi yangi kartalar limiti tugadi — ertaga davom etamiz." : "Bu bo‘limda takrorlash vaqti kelgan karta yo‘q."}
          </p>
        )}
        <div className="mt-2 flex w-full max-w-[360px] flex-col gap-2">
          {doneSome && queue.new_left + queue.due > 0 && (
            <button type="button" onClick={() => { setStats({ knew: 0, forgot: 0 }); setRound((r) => r + 1); }}
              className="rounded-full bg-cta py-3.5 text-[15px] font-bold text-on-cta">Yana davom etish</button>
          )}
          <button type="button" onClick={() => { void reload(); navigate("/", true); }}
            className="rounded-full border border-line-strong bg-surface py-3.5 text-[15px] font-bold text-ink">Bosh sahifa</button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pb-[calc(var(--safe-bottom)+150px)]">
      {/* Yuqori panel */}
      <div className={cx(wrap, "sticky top-0 z-10 flex items-center gap-3 bg-canvas/90 pb-3 pt-[calc(var(--safe-top)+12px)] backdrop-blur")}>
        <button type="button" onClick={quit} aria-label="Yopish" className="grid h-9 w-9 place-items-center rounded-full text-muted hover:bg-surface-2">
          <Close size={20} />
        </button>
        <Bar value={(idx + (back ? 1 : 0)) / total} className="flex-1" tone="bg-peri" />
        <span className="text-[13px] font-bold tabular-nums text-muted">{idx + 1}/{total}</span>
      </div>

      <div className={wrap}>
        <div key={card.fact_id} className="rise rounded-card border border-line bg-surface p-5 shadow-lift">
          <div className="flex flex-wrap items-center gap-1.5">
            <Pill className={TONE[card.tur] ?? "bg-surface-2 text-muted"}>{card.label}</Pill>
            <Pill>{card.davr}</Pill>
            <Pill>{card.sinf}-sinf</Pill>
          </div>

          <div className="mt-5 text-[13px] font-bold uppercase tracking-[.1em] text-muted">{card.prompt}</div>
          {card.body && <p className="mt-2 font-reading text-[21px] leading-[1.45] text-ink">{card.body}</p>}
          {card.hints.length > 0 && (
            <ol className="mt-3 space-y-2">
              {card.hints.map((h, i) => (
                <li key={i} className="flex gap-3 rounded-2xl bg-surface-2/70 px-3.5 py-2.5 text-[15.5px] leading-snug text-ink">
                  <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full bg-shaxs-soft text-[12px] font-bold text-shaxs">{i + 1}</span>
                  <span className="font-reading">{h}</span>
                </li>
              ))}
            </ol>
          )}

          {!back ? (
            <p className="mt-6 border-t border-dashed border-line pt-4 text-center text-[13.5px] text-faint">
              Avval o‘zingiz eslang, keyin javobni oching
            </p>
          ) : (
            <div className="rise mt-5 border-t border-line pt-5">
              <div className="text-[12px] font-bold uppercase tracking-[.1em] text-success">Javob</div>
              <div className="mt-1 text-[22px] font-extrabold leading-tight tracking-tight text-ink">{back.answer}</div>
              {back.text && back.text !== back.answer && (
                <p className="mt-3 font-reading text-[16px] leading-relaxed text-ink-2">{back.text}</p>
              )}
              {back.extra.map((x) => <p key={x} className="mt-1.5 text-[14px] text-muted">{x}</p>)}

              <div className="mt-4 rounded-2xl bg-surface-2/70 p-3.5">
                <div className="flex items-start gap-2.5 text-[13.5px] font-semibold text-ink-2">
                  <Book size={17} className="mt-0.5 shrink-0 text-peri" />
                  <span>{back.source}{back.mavzu && <span className="font-normal text-muted"> · {back.mavzu}</span>}</span>
                </div>
                {back.iqtibos && (
                  <button type="button" onClick={() => setShowQuote(!showQuote)} className="mt-2 text-[13px] font-semibold text-peri">
                    {showQuote ? "Iqtibosni yashirish" : "Darslikdan iqtibos"}
                  </button>
                )}
                {showQuote && <p className="mt-1.5 font-reading text-[14.5px] italic leading-relaxed text-ink-2">«{back.iqtibos}»</p>}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Pastki tugmalar */}
      <div className="fixed inset-x-0 bottom-0 z-20 border-t border-line bg-surface/95 backdrop-blur">
        <div className={cx(wrap, "py-3 pb-[calc(var(--safe-bottom)+12px)]")}>
          {!back ? (
            <button type="button" disabled={busy} onClick={reveal}
              className="w-full rounded-full bg-cta py-3.5 text-[16px] font-bold text-on-cta transition active:scale-[.99] disabled:opacity-60">
              Javobni ko‘rish
            </button>
          ) : (
            <>
              <div className="mb-2 text-center text-[13px] font-semibold text-muted">Bildingizmi?</div>
              <div className="grid grid-cols-2 gap-3">
                <button type="button" disabled={busy} onClick={() => grade(false)}
                  className="rounded-full bg-danger-soft py-3.5 text-[16px] font-bold text-danger transition active:scale-[.98] disabled:opacity-60">
                  Bilmadim
                </button>
                <button type="button" disabled={busy} onClick={() => grade(true)}
                  className="rounded-full bg-success py-3.5 text-[16px] font-bold text-on-success transition active:scale-[.98] disabled:opacity-60">
                  Bildim
                </button>
              </div>
              <div className="mt-2 flex justify-between px-2 text-[11.5px] text-faint">
                <span>10 daqiqadan keyin qaytadi</span><span>oraliq oshadi</span>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
