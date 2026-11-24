// O'zbek lotin -> kirill. backend/app/services/translit.py ning aynan nusxasi.
// Ikkalasi ham backend/tests/translit_cases.json bilan tekshiriladi (npm test, pytest).

const APOSTROPHES = "'ʻʼ‘’`";
const SINGLE: Record<string, string> = {
  a: "а", b: "б", d: "д", e: "е", f: "ф", g: "г", h: "ҳ", i: "и", j: "ж", k: "к", l: "л",
  m: "м", n: "н", o: "о", p: "п", q: "қ", r: "р", s: "с", t: "т", u: "у", v: "в", x: "х",
  y: "й", z: "з", c: "ц", w: "в",
};
const Y_VOWELS: Record<string, string> = { o: "ё", u: "ю", a: "я", e: "е" };
const VOWELS = new Set("aeiouAEIOU");
// Rim raqamlari (XIV asr, Pyotr I, Kir II) o'girilmaydi
const SKIP = /(<[^>]+>|&#?\w+;|\{[^}]*\}|https?:\/\/\S+|\bXP\b|\b[IVXLCDM]+\b)/;

const isApo = (ch: string) => ch !== "" && APOSTROPHES.includes(ch);
const isAlpha = (ch: string) => ch !== "" && ch.toLowerCase() !== ch.toUpperCase();
const withCase = (src: string, cyr: string) => (src !== src.toLowerCase() ? cyr.toUpperCase() : cyr);

function convert(text: string): string {
  const out: string[] = [];
  let i = 0;
  const n = text.length;
  while (i < n) {
    const ch = text[i];
    const low = ch.toLowerCase();
    const nxt = text[i + 1] ?? "";
    const nxt2 = text[i + 2] ?? "";

    if ((low === "o" || low === "g") && isApo(nxt)) {
      out.push(withCase(ch, low === "o" ? "ў" : "ғ"));
      i += 2;
      continue;
    }
    if ((low === "s" || low === "c") && nxt.toLowerCase() === "h") {
      out.push(withCase(ch, low === "s" ? "ш" : "ч"));
      i += 2;
      continue;
    }
    if (low === "y" && nxt.toLowerCase() in Y_VOWELS && !(nxt.toLowerCase() === "o" && isApo(nxt2))) {
      out.push(withCase(ch, Y_VOWELS[nxt.toLowerCase()]));
      i += 2;
      continue;
    }
    if (low === "e") {
      const prev = i > 0 ? text[i - 1] : "";
      const atStart = !isAlpha(prev) && !isApo(prev);
      out.push(withCase(ch, atStart || VOWELS.has(prev) ? "э" : "е"));
      i += 1;
      continue;
    }
    if (isApo(ch) && i > 0 && isAlpha(text[i - 1])) {
      out.push("ъ");
      i += 1;
      continue;
    }
    out.push(low in SINGLE ? withCase(ch, SINGLE[low]) : ch);
    i += 1;
  }
  return out.join("");
}

export function toCyrillic(text: string): string {
  if (!text) return text;
  return text
    .split(SKIP)
    .map((part, idx) => (idx % 2 ? part : convert(part)))
    .join("");
}

export type Alphabet = "latn" | "cyrl";
export const tr = (text: string, a: Alphabet) => (a === "cyrl" ? toCyrillic(text) : text);
