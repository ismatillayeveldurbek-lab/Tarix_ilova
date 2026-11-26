// Telegram Mini App bilan ishlash (https://core.telegram.org/bots/webapps)

type Haptic = {
  impactOccurred(style: "light" | "medium" | "heavy" | "rigid" | "soft"): void;
  notificationOccurred(type: "error" | "success" | "warning"): void;
  selectionChanged(): void;
};

type TgWebApp = {
  initData: string;
  colorScheme: "light" | "dark";
  ready(): void;
  expand(): void;
  close(): void;
  setHeaderColor?(color: string): void;
  setBackgroundColor?(color: string): void;
  disableVerticalSwipes?(): void;
  enableClosingConfirmation?(): void;
  disableClosingConfirmation?(): void;
  showConfirm?(message: string, cb: (ok: boolean) => void): void;
  openTelegramLink?(url: string): void;
  HapticFeedback?: Haptic;
  BackButton?: { show(): void; hide(): void; onClick(cb: () => void): void; offClick(cb: () => void): void };
  onEvent?(event: string, cb: () => void): void;
  version?: string;
};

declare global {
  interface Window {
    Telegram?: { WebApp: TgWebApp };
  }
}

export const tg: TgWebApp | undefined = window.Telegram?.WebApp;

export function initTelegram(): void {
  if (!tg) return;
  tg.ready();
  tg.expand();
  try {
    tg.disableVerticalSwipes?.();
  } catch {
    /* eski Telegram versiyalari */
  }
}

export const getInitData = (): string => tg?.initData || "";

export function colorScheme(): "light" | "dark" {
  if (tg?.initData) return tg.colorScheme;
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function applyTheme(): void {
  const scheme = colorScheme();
  document.documentElement.dataset.theme = scheme;
  const bg = getComputedStyle(document.documentElement).getPropertyValue("--bg").trim();
  try {
    tg?.setHeaderColor?.(bg);
    tg?.setBackgroundColor?.(bg);
  } catch {
    /* ignore */
  }
}

export const haptic = {
  success: () => tg?.HapticFeedback?.notificationOccurred("success"),
  error: () => tg?.HapticFeedback?.notificationOccurred("error"),
  tap: () => tg?.HapticFeedback?.impactOccurred("light"),
  select: () => tg?.HapticFeedback?.selectionChanged(),
};

/** Telegram ichida bo‘lsa uning oynasi, aks holda brauzer confirm(). */
export function confirmDialog(message: string): Promise<boolean> {
  return new Promise((resolve) => {
    if (tg?.initData && tg.showConfirm) {
      try {
        tg.showConfirm(message, resolve);
        return;
      } catch {
        /* fallback */
      }
    }
    resolve(window.confirm(message));
  });
}

/** Telegram’ning "ulashish" oynasi: do‘stni tanlab, havolani yuborish */
export function shareLink(url: string, text: string): void {
  const share = `https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`;
  if (tg?.initData && tg.openTelegramLink) tg.openTelegramLink(share);
  else window.open(share, "_blank", "noopener");
}

/** Matnni nusxalash (eski brauzerlar uchun zaxira usul bilan) */
export async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    const ok = document.execCommand("copy");
    ta.remove();
    return ok;
  }
}
