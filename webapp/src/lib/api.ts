// Server bilan aloqa. Telegram ichida initData, brauzerdagi admin panelda esa token yuboriladi.
import { getInitData } from "./telegram";

const TOKEN_KEY = "tarix_admin_token";

export function setAdminToken(token: string): void {
  try {
    sessionStorage.setItem(TOKEN_KEY, token);
  } catch {
    memoryToken = token;
  }
  memoryToken = token;
}

let memoryToken = "";
function adminToken(): string {
  try {
    return sessionStorage.getItem(TOKEN_KEY) || memoryToken;
  } catch {
    return memoryToken;
  }
}

function authHeaders(): Record<string, string> {
  const init = getInitData();
  if (init) return { Authorization: `tma ${init}` };
  const token = adminToken();
  if (token) return { Authorization: `Bearer ${token}` };
  return {};
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

type Options = { method?: string; body?: unknown; form?: FormData };

export async function api<T = unknown>(path: string, opts: Options = {}): Promise<T> {
  const headers: Record<string, string> = authHeaders();
  let body: BodyInit | undefined;
  if (opts.form) body = opts.form;
  else if (opts.body !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(opts.body);
  }
  let res: Response;
  try {
    res = await fetch(`/api${path}`, { method: opts.method || (body ? "POST" : "GET"), headers, body });
  } catch {
    throw new ApiError("Internet aloqasi yo‘q. Qayta urinib ko‘ring", 0);
  }
  if (!res.ok) {
    let message = `Xatolik (${res.status})`;
    try {
      const data = await res.json();
      if (typeof data.detail === "string") message = data.detail;
      else if (Array.isArray(data.detail)) message = "Maydonlar noto‘g‘ri to‘ldirilgan";
    } catch {
      /* JSON emas */
    }
    throw new ApiError(message, res.status);
  }
  return res.json() as Promise<T>;
}

/** Fayl yuklab olish (masalan, Excel shablon). */
export async function download(path: string, filename: string): Promise<void> {
  const res = await fetch(`/api${path}`, { headers: authHeaders() });
  if (!res.ok) throw new ApiError("Fayl yuklab olinmadi", res.status);
  const url = URL.createObjectURL(await res.blob());
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
