import { useCallback, useEffect, useState } from "react";
import { api } from "../../lib/api";
import { toast } from "../../components/ui";

export type AdminTopic = { id: number; name: string; sort_order: number; period_id: number | null; questions: number };
export type AdminPeriod = { id: number; name: string; sort_order: number; questions: number; topics: AdminTopic[] };
export type AdminQuestion = {
  id: number; text: string; a: string; b: string; c: string; d: string; correct: "a" | "b" | "c" | "d";
  explanation: string; difficulty: number; period_id: number | null; topic_id: number | null;
  period: string | null; topic: string | null; is_active: boolean;
};
export type ImportReport = { added: number; skipped_duplicates: number; errors: string[] };

export function usePeriods() {
  const [periods, setPeriods] = useState<AdminPeriod[]>([]);
  const reload = useCallback(async () => {
    try {
      setPeriods(await api<AdminPeriod[]>("/admin/periods"));
    } catch (e) {
      toast((e as Error).message, "error");
    }
  }, []);
  useEffect(() => { void reload(); }, [reload]);
  return { periods, reload };
}

export const DIFFICULTY = ["", "Oson", "O'rta", "Qiyin"];
