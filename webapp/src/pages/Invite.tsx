import { useEffect, useState } from "react";
import { Check, Copy, Share, Users } from "../components/Icons";
import { Avatar, Loading, toast } from "../components/ui";
import { api } from "../lib/api";
import { copyText, haptic, shareLink } from "../lib/telegram";
import type { Referrals } from "../lib/types";

const SHARE_TEXT = "Tarixdan milliy sertifikatga birga tayyorlanamiz: har kuni 10 ta savol, izohlar va sinov imtihoni.";

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
    <div className="page stack">
      <div className="page-head">
        <div>
          <div className="eyebrow">Taklif dasturi</div>
          <h1>Do‘stlarni taklif qilish</h1>
          <p className="muted small" style={{ marginTop: 4 }}>Birga tayyorlanish samaraliroq. Har bir faol do‘st uchun bonus XP oling.</p>
        </div>
      </div>

      <div className="card stack" style={{ gap: 12 }}>
        {steps.map((text, i) => (
          <div key={i} className="row" style={{ alignItems: "flex-start" }}>
            <span className="step-num">{i + 1}</span>
            <span className="small" style={{ paddingTop: 2 }}>{text}</span>
          </div>
        ))}
      </div>

      <div className="stack" style={{ gap: 8 }}>
        <div className="eyebrow">Sizning havolangiz</div>
        <div className="link-box">
          <span className="ellipsis grow">{data.link.replace("https://", "")}</span>
          <button className="btn sm white" onClick={copy}>
            {copied ? <><Check size={15} /> Nusxalandi</> : <><Copy size={15} /> Nusxalash</>}
          </button>
        </div>
        <button className="btn block" onClick={() => { haptic.tap(); shareLink(data.link, SHARE_TEXT); }}>
          <Share size={18} /> Telegram orqali yuborish
        </button>
      </div>

      <div className="metrics">
        <div className="metric"><span className="label">Taklif qilingan</span><span className="value">{data.invited}</span></div>
        <div className="metric"><span className="label">Faol</span><span className="value">{data.active}</span></div>
        <div className="metric"><span className="label">Topilgan</span><span className="value">{data.earned_xp}<small>XP</small></span></div>
      </div>

      <div className="section-title"><span>Do‘stlaringiz</span></div>
      {data.friends.length === 0 ? (
        <div className="card empty">
          <span className="empty-icon"><Users size={24} /></span>
          <div className="muted small">Hali hech kim qo‘shilmadi. Havolani birinchi do‘stingizga yuboring.</div>
        </div>
      ) : (
        <div className="card list" style={{ padding: "4px 10px" }}>
          {data.friends.map((f, i) => (
            <div key={i} className="list-row">
              <Avatar name={f.name} />
              <div className="grow">
                <div style={{ fontWeight: 500 }}>{f.name}</div>
                <div className="tiny muted">{new Date(f.joined_at).toLocaleDateString()}</div>
              </div>
              {f.active
                ? <span className="chip green">+{data.xp_inviter} XP</span>
                : <span className="chip">{data.min_answers} ta savol kutilmoqda</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
