import type { Alphabet } from "./translit";

export type Option = { key: "a" | "b" | "c" | "d"; text: string };

export type Question = {
  id: number;
  text: string;
  options: Option[];
  period: string | null;
  topic: string | null;
  difficulty: number;
  chosen?: string;
};

export type TopicNode = { id: number; name: string; total: number; solved: number };
export type PeriodNode = { id: number; name: string; topics: TopicNode[] };

export type Home = {
  user: {
    name: string;
    alphabet: Alphabet;
    alphabet_chosen: boolean;
    is_admin: boolean;
    streak: number;
    streak_best: number;
    reminder_enabled: boolean;
    reminder_time: string;
  };
  today: { done: number; goal: number };
  week: { xp: number; rank: number | null; days: { date: string; weekday: number; active: boolean }[] };
  totals: { answers: number; correct: number };
  due_count: number;
  path: PeriodNode[];
  exam: { name: string; count: number; minutes: number } | null;
  history_today: { year: number | null; title: string; text: string }[];
};

export type AnswerResult = {
  is_correct: boolean;
  correct_option: string;
  explanation: string;
  xp: number;
  streak: number;
  streak_increased: boolean;
  today_done: number;
  goal: number;
  goal_reached: boolean;
};
