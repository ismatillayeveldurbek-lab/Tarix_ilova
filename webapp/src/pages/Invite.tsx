import { useEffect, useState } from "react";
import { Check, Star } from "../components/Icons";
import { Mascot } from "../components/Mascot";
import { Avatar, Loading, toast } from "../components/ui";
import { api } from "../lib/api";
import { copyText, haptic, shareLink } from "../lib/telegram";
import type { Referrals } from "../lib/types";

const SHARE_TEXT = "Tarixdan milliy sertifikatga birga tayyorlanamiz! Har kuni 10 ta savol, izohlar va sinov imtihoni 📜";

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
    } else toast("Nusxalab bo'lmadi", "error");
  }

  const steps: [string, string][] = [
    ["📤", "Havolani do'stingizga yuboring"],
    ["📝", `Do'stingiz botga kirib, ${data.min_answers} ta savol yechadi`],
    ["🎁", `Sizga +${data.xp_inviter} XP, do'stingizga +${data.xp_invited} XP`],
  ];

  return (
    <div className="page stack">
      <div className="invite-hero">
        <Avatar name="Siz" seed={3} size="lg" />
        <Mascot size={110} mood="wow" className="bob" />
        <Avatar name="Do'st" seed={1} size="lg" />
      </div>
      <div className="center stack" style={{ gap: 4 }}>
        <h1 style={{ fontSize: 24 }}>Do'stlaringizni taklif qiling</h1>
        <p className="muted">Birga o'qish qiziqroq — va har bir do'st uchun XP!</p>
      </div>

      <div className="card stack" style={{ gap: 10 }}>
        {steps.map(([icon, text], i) => (
          <div key={i} className="row">
            <span className="step-num">{i + 1}</span>
            <span style={{ fontSize: 22 }}>{icon}</span>
            <span className="bold small">{text}</span>
          </div>
        ))}
      </div>

      <div className="link-box">
        <span className="ellipsis grow">{data.link.replace("https://", "")}</span>
        <button className={`btn sm ${copied ? "" : "white"}`} onClick={copy}>
          {copied ? <><Check size={16} /> Nusxalandi</> : "Nusxalash"}
        </button>
      </div>
      <button className="btn blue block" onClick={() => { haptic.tap(); shareLink(data.link, SHARE_TEXT); }}>
        📤 Do'stga yuborish
      </button>

      <div className="tiles">
        <div className="tile blue"><div className="label">Taklif</div><div className="value">{data.invited}</div></div>
        <div className="tile green"><div className="label">Faol</div><div className="value">{data.active}</div></div>
        <div className="tile gold"><div className="label">Topilgan</div><div className="value"><Star size={20} />{data.earned_xp}</div></div>
      </div>

      <div className="section-title">Do'stlaringiz</div>
      {data.friends.length === 0 ? (
        <div className="card empty" style={{ padding: 20 }}>
          <Mascot mood="think" size={80} />
          <div className="muted small">Hali hech kim qo'shilmadi. Havolani birinchi do'stingizga yuboring!</div>
        </div>
      ) : (
        <div className="card list" style={{ padding: 8 }}>
          {data.friends.map((f, i) => (
            <div key={i} className="list-row">
              <Avatar name={f.name} />
              <div className="grow">
                <div className="bold">{f.name}</div>
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
