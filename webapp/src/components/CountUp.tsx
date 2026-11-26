import { useEffect, useState } from "react";

/** Raqam 0 dan qiymatgacha sanab chiqadi (natija ekranlari uchun) */
export function CountUp({ value, duration = 900, suffix = "" }: { value: number; duration?: number; suffix?: string }) {
  const [n, setN] = useState(0);
  useEffect(() => {
    let frame = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const p = Math.min(1, (now - start) / duration);
      setN(Math.round(value * (1 - Math.pow(1 - p, 3))));
      if (p < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value, duration]);
  return <>{n}{suffix}</>;
}
