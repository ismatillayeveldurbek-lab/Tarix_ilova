export type Option = { key: "a" | "b" | "c" | "d"; text: string };

export type Question = {
  id: number;
  text: string;
  options: Option[];
  period: string | null;
  topic: string | null;
  difficulty: number;
  image: string | null;
  chosen?: string;
};

export type TopicNode = { id: number; name: string; total: number; solved: number; percent: number };
export type PeriodNode = { id: number; name: string; topics: TopicNode[] };

export type Home = {
  user: {
    name: string;
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
  mastery: number;
  recommendation: Recommendation | null;
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

/** Mavzu bo'yicha natija */
export type TopicProgress = {
  id: number; name: string; period: string | null; total: number; mastered: number; answered: number;
  attempts: number; percent: number; accuracy: number | null;
};
export type Recommendation = TopicProgress & { kind: "weak" | "new" };
export type Progress = {
  overall: number; mastered: number; total: number;
  periods: { id: number; name: string; percent: number; total: number; topics: TopicProgress[] }[];
  weak: TopicProgress[];
  recommendation: Recommendation | null;
};
