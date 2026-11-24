// Mini App'dagi o'girish Python versiyasi bilan bir xil ishlashini tekshiradi.
import { readFileSync } from "node:fs";
import { toCyrillic } from "../src/lib/translit.ts";

const cases = JSON.parse(readFileSync(new URL("../../backend/tests/translit_cases.json", import.meta.url)));
let failed = 0;
for (const [latn, cyrl] of cases) {
  const got = toCyrillic(latn);
  if (got !== cyrl) {
    failed++;
    console.error(`✗ ${latn} -> ${got} (kutilgan: ${cyrl})`);
  }
}
console.log(failed ? `${failed} ta xato` : `✓ ${cases.length} ta holat to'g'ri`);
process.exit(failed ? 1 : 0);
