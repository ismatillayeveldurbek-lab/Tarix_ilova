import { useEffect, useState } from "react";
import { CountUp } from "../components/CountUp";
import { Check, Copy, Share, Users } from "../components/Icons";
import { Card, HeroCard, Initials, Pill, Screen, SectionTitle, cx } from "../components/kit";
import { Loading, toast } from "../components/ui";
import { api } from "../lib/api";
import { copyText, haptic, shareLink } from "../lib/telegram";
import type { Referrals } from "../lib/types";

const SHARE_TEXT = "Tarixdan milliy sertifikatga birga tayyorlanamiz: har kuni mashq, izohlar va sinov imtihoni.";

export function InvitePage() {
  const [data, setData] = useState<Referrals | null>(null);
  const [copied, setCopied] = useState(false);
  useEffect(() => { api<Referrals>("/referrals").then(setData).catch((e) => toast(e.message, "error")); }, []);
  if (!data) return <Loading />;

  async function copy() {
    if (await copyText(data!.link)) {
      haptic.success();
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } else toast("Nusxalab bo‘lmadi", "error");
  }

  const steps = [
    "Shaxsiy havolangizni do‘stingizga yuboring",
    `Do‘stingiz botga kirib, ${data.min_answers} ta savol yechadi`,
    `Sizga +${data.xp_inviter} XP, do‘stingizga +${data.xp_invited} XP beriladi`,
  ];

  return (
    <Screen>
      <HeroCard>
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-[12px] font-semibold uppercase tracking-[.12em] text-white/65">Taklif dasturi</div>
            <h1 className="mt-1 text-[24px] font-extrabold leading-tight tracking-tight">Do‘stlar bilan birga tayyorlaning</h1>
            <p className="mt-1 text-[13.5px] text-white/65">Har bir faol do‘st uchun +{data.xp_inviter} XP</p>
          </div>
          <span className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-white/12"><Users size={24} className="animate-breathe" /></span>
        </div>
        <div className="mt-5 grid grid-cols-3 gap-2">
          {[["Taklif qilingan", data.invited], ["Faol", data.active], ["Topilgan XP", data.earned_xp]].map(([l, v]) => (
            <div key={String(l)} className="rounded-2xl bg-white/[.08] px-3 py-2.5">
              <div className="text-[11.5px] font-medium text-white/60">{l}</div>
              <div className="text-[20px] font-bold tabular-nums"><CountUp value={Number(v)} /></div>
            </div>
          ))}
        </div>
      </HeroCard>

      <Card className="space-y-3 p-4">
        {steps.map((text, i) => (
          <div key={i} className="flex items-start gap-3">
            <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-peri-soft text-[13px] font-bold text-peri">{i + 1}</span>
            <span className="pt-0.5 text-[14.5px] text-ink">{text}</span>
          </div>
        ))}
      </Card>

      <div className="space-y-2.5">
        <SectionTitle>Sizning havolangiz</SectionTitle>
        <div className="flex items-center gap-2 rounded-2xl border border-line bg-surface p-1.5 pl-4 shadow-soft">
          <span className="min-w-0 flex-1 truncate text-[14px] font-medium text-ink-2">{data.link.replace("https://", "")}</span>
          <button type="button" onClick={copy}
            className={cx("inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-[13.5px] font-bold transition",
              copied ? "bg-success-soft text-success" : "bg-surface-2 text-ink hover:bg-line")}>
            {copied ? <><Check size={15} className="animate-pop" /> Nusxalandi</> : <><Copy size={15} /> Nusxalash</>}
          </button>
        </div>
        <button type="button" onClick={() => { haptic.tap(); shareLink(data.link, SHARE_TEXT); }}
          className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-cta py-3.5 text-[15.5px] font-bold text-on-cta transition active:scale-[.99]">
          <Share size={18} /> Telegram orqali yuborish
        </button>
      </div>

      <SectionTitle>Do‘stlaringiz</SectionTitle>
      {data.friends.length === 0 ? (
        <Card className="flex flex-col items-center gap-2 p-7 text-center">
          <span className="grid h-14 w-14 animate-pop place-items-center rounded-2xl bg-joy-soft text-joy"><Users size={26} /></span>
          <div className="text-[14px] text-muted">Hali hech kim qo‘shilmadi. Havolani birinchi do‘stingizga yuboring.</div>
        </Card>
      ) : (
        <Card className="stagger divide-y divide-line overflow-hidden">
          {data.friends.map((f, i) => (
            <div key={i} className="flex items-center gap-3 px-4 py-3">
              <Initials name={f.name} size={40} />
              <div className="min-w-0 flex-1">
                <div className="truncate text-[15px] font-semibold text-ink">{f.name}</div>
                <div className="text-[12.5px] text-muted">{new Date(f.joined_at).toLocaleDateString()}</div>
              </div>
              {f.active
                ? <Pill className="bg-success-soft text-success">+{data.xp_inviter} XP</Pill>
                : <Pill>{data.min_answers} ta savol kutilmoqda</Pill>}
            </div>
          ))}
        </Card>
      )}
    </Screen>
  );
}
