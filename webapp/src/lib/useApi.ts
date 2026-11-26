import { useCallback, useEffect, useState } from "react";
import { api } from "./api";

/** GET so‘rov uchun oddiy hook: { data, error, reload } */
export function useApi<T>(path: string | null) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const reload = useCallback(async () => {
    if (!path) return;
    try {
      setData(await api<T>(path));
      setError(null);
    } catch (e) {
      setError((e as Error).message);
    }
  }, [path]);
  useEffect(() => { void reload(); }, [reload]);
  return { data, error, reload };
}
