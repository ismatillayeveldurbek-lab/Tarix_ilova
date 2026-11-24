// "Tarixchi" — ilova qahramoni: qadimiy o'ram (qo'lyozma). Kayfiyati o'zgaradi.
type Mood = "happy" | "sad" | "wow" | "think";

export function Mascot({ mood = "happy", size = 120, className = "" }: { mood?: Mood; size?: number; className?: string }) {
  const mouth = {
    happy: <path d="M50 74 Q60 84 70 74" stroke="#5b3a1a" strokeWidth="4" fill="none" strokeLinecap="round" />,
    sad: <path d="M50 80 Q60 72 70 80" stroke="#5b3a1a" strokeWidth="4" fill="none" strokeLinecap="round" />,
    wow: <ellipse cx="60" cy="78" rx="6" ry="7" fill="#5b3a1a" />,
    think: <path d="M52 78 H68" stroke="#5b3a1a" strokeWidth="4" strokeLinecap="round" />,
  }[mood];
  const eyeY = mood === "sad" ? 60 : 58;
  return (
    <svg width={size} height={size} viewBox="0 0 120 120" className={className} aria-hidden>
      <ellipse cx="60" cy="112" rx="30" ry="5" fill="rgba(0,0,0,.12)" />
      {/* tana — o'ram */}
      <rect x="26" y="22" width="68" height="80" rx="10" fill="#f8e3b0" stroke="#d9b56c" strokeWidth="3" />
      {/* yuqori va pastki o'ralgan qismlar */}
      <rect x="18" y="14" width="84" height="16" rx="8" fill="#e8c27a" stroke="#b98d3e" strokeWidth="3" />
      <rect x="18" y="94" width="84" height="16" rx="8" fill="#e8c27a" stroke="#b98d3e" strokeWidth="3" />
      <circle cx="18" cy="22" r="6" fill="#b5834a" />
      <circle cx="102" cy="22" r="6" fill="#b5834a" />
      <circle cx="18" cy="102" r="6" fill="#b5834a" />
      <circle cx="102" cy="102" r="6" fill="#b5834a" />
      {/* ko'zlar */}
      <ellipse cx="47" cy={eyeY} rx="9" ry="10" fill="#fff" />
      <ellipse cx="73" cy={eyeY} rx="9" ry="10" fill="#fff" />
      <circle cx={mood === "think" ? 50 : 48} cy={eyeY + 1} r="5" fill="#2b2118" />
      <circle cx={mood === "think" ? 76 : 74} cy={eyeY + 1} r="5" fill="#2b2118" />
      <circle cx="50" cy={eyeY - 2} r="1.8" fill="#fff" />
      <circle cx="76" cy={eyeY - 2} r="1.8" fill="#fff" />
      {mood === "sad" && (
        <>
          <path d="M38 46 L54 50" stroke="#5b3a1a" strokeWidth="3" strokeLinecap="round" />
          <path d="M82 46 L66 50" stroke="#5b3a1a" strokeWidth="3" strokeLinecap="round" />
        </>
      )}
      {/* yonoqlar */}
      <ellipse cx="38" cy="74" rx="6" ry="4" fill="#f4a3a3" opacity=".7" />
      <ellipse cx="82" cy="74" rx="6" ry="4" fill="#f4a3a3" opacity=".7" />
      {mouth}
      {/* qo'lyozma chiziqlari */}
      <path d="M40 38 H80 M44 44 H76" stroke="#d9b56c" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  );
}
