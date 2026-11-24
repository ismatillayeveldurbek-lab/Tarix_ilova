// Ilova ikonkalari (SVG). currentColor — atrofdagi matn rangini oladi.
type P = { size?: number; className?: string };
const S = ({ size = 24, className, children, fill = "none" }: P & { children: React.ReactNode; fill?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill={fill} className={className}
    stroke="currentColor" strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    {children}
  </svg>
);

export const Flame = ({ size = 24, className }: P) => (
  <svg width={size} height={size} viewBox="0 0 24 24" className={className} aria-hidden>
    <path d="M12 2c1 3.5 5.5 6 5.5 11a5.5 5.5 0 0 1-11 0c0-2.6 1.4-4.2 2.6-5.4.3 1.6 1 2.6 2 3.1C11 8.2 10.6 5 12 2z" fill="#ff8a1f" />
    <path d="M12 12.2c.7 1.6 2.6 2.6 2.6 4.6a2.6 2.6 0 0 1-5.2 0c0-1.5.9-2.5 1.8-3.2.1.6.4 1 .8 1.2-.2-1 0-1.8 0-2.6z" fill="#ffd34d" />
  </svg>
);

export const Star = ({ size = 24, className }: P) => (
  <svg width={size} height={size} viewBox="0 0 24 24" className={className} aria-hidden>
    <path d="M12 2.5l2.9 6 6.6.8-4.9 4.6 1.3 6.6L12 17.3l-5.9 3.2 1.3-6.6L2.5 9.3l6.6-.8z" fill="#f6b200" stroke="#c88d00" strokeWidth="1.4" strokeLinejoin="round" />
  </svg>
);

export const Target = ({ size = 24, className }: P) => (
  <svg width={size} height={size} viewBox="0 0 24 24" className={className} aria-hidden>
    <circle cx="12" cy="12" r="10" fill="#2d9cdb" />
    <circle cx="12" cy="12" r="6.5" fill="#fff" />
    <circle cx="12" cy="12" r="3.2" fill="#2d9cdb" />
  </svg>
);

export const Crown = ({ size = 24, className }: P) => (
  <svg width={size} height={size} viewBox="0 0 24 24" className={className} aria-hidden>
    <path d="M3 8l4.5 3.5L12 5l4.5 6.5L21 8l-2 11H5z" fill="#fff" stroke="#fff" strokeWidth="1.5" strokeLinejoin="round" />
  </svg>
);

export const Home = (p: P) => <S {...p}><path d="M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z" /></S>;
export const Trophy = (p: P) => <S {...p}><path d="M7 4h10v5a5 5 0 0 1-10 0zM7 6H4a3 3 0 0 0 3 4M17 6h3a3 3 0 0 1-3 4M12 14v4M8 21h8M9 18h6" /></S>;
export const User = (p: P) => <S {...p}><circle cx="12" cy="8" r="4" /><path d="M4 21a8 8 0 0 1 16 0" /></S>;
export const Clipboard = (p: P) => <S {...p}><rect x="5" y="4" width="14" height="17" rx="2" /><path d="M9 4V3h6v1M9 11l2 2 4-4M9 17h6" /></S>;
export const Shield = (p: P) => <S {...p}><path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z" /><path d="M9 12l2 2 4-4" /></S>;
export const Close = (p: P) => <S {...p}><path d="M6 6l12 12M18 6L6 18" /></S>;
export const Check = (p: P) => <S {...p}><path d="M5 12.5l4.5 4.5L19 7" /></S>;
export const Cross = (p: P) => <S {...p}><path d="M7 7l10 10M17 7L7 17" /></S>;
export const Flag = (p: P) => <S {...p}><path d="M5 21V4M5 4h11l-2 4 2 4H5" /></S>;
export const Clock = (p: P) => <S {...p}><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></S>;
export const Book = (p: P) => <S {...p}><path d="M4 5a2 2 0 0 1 2-2h13v15H6a2 2 0 0 0-2 2zM4 20a2 2 0 0 0 2 1h13" /></S>;
export const Refresh = (p: P) => <S {...p}><path d="M20 11a8 8 0 0 0-14.3-4.9L4 8M4 4v4h4M4 13a8 8 0 0 0 14.3 4.9L20 16M20 20v-4h-4" /></S>;
export const Calendar = (p: P) => <S {...p}><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></S>;
export const Upload = (p: P) => <S {...p}><path d="M12 16V4M7 9l5-5 5 5M4 17v3h16v-3" /></S>;
export const Download = (p: P) => <S {...p}><path d="M12 4v12M7 11l5 5 5-5M4 17v3h16v-3" /></S>;
export const Trash = (p: P) => <S {...p}><path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3" /></S>;
export const Edit = (p: P) => <S {...p}><path d="M4 20h4L19 9l-4-4L4 16zM14 6l4 4" /></S>;
export const Plus = (p: P) => <S {...p}><path d="M12 5v14M5 12h14" /></S>;
export const Search = (p: P) => <S {...p}><circle cx="11" cy="11" r="7" /><path d="M20 20l-4-4" /></S>;
export const Layers = (p: P) => <S {...p}><path d="M12 3l9 5-9 5-9-5zM3 13l9 5 9-5" /></S>;
export const Chart = (p: P) => <S {...p}><path d="M4 20V10M10 20V4M16 20v-7M22 20H2" /></S>;
export const Bell = (p: P) => <S {...p}><path d="M6 16V11a6 6 0 0 1 12 0v5l2 2H4zM10 21h4" /></S>;
export const Globe = (p: P) => <S {...p}><circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3c3 3.5 3 14.5 0 18M12 3c-3 3.5-3 14.5 0 18" /></S>;
export const ChevronRight = (p: P) => <S {...p}><path d="M9 6l6 6-6 6" /></S>;
export const ChevronLeft = (p: P) => <S {...p}><path d="M15 6l-6 6 6 6" /></S>;
export const Lightning = (p: P) => <S {...p} fill="currentColor"><path d="M13 2L4 14h7l-1 8 9-12h-7z" strokeWidth={1.5} /></S>;
