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

export type TopicNode = { id: number; name: string; total: number; solved: number; percent: number; book?: string | null };
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
  referral_bonus: number;
};

export type Referrals = {
  link: string; min_answers: number; xp_inviter: number; xp_invited: number;
  invited: number; active: number; earned_xp: number;
  friends: { name: string; joined_at: string; active: boolean }[];
};

/** Mavzu bo‘yicha natija */
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

/** /api/v1/path — "Tarix yo‘lingiz" */
export type FactPath = {
  total: number;
  mastered: number;
  davrlar: { name: string; total: number; mastered: number; started: number }[];
  sections: { tur: "sana" | "shaxs" | "atama" | "joy" | "urush" | "asar"; label: string; total: number }[];
};

/** /api/v1/cards/summary — bo'limlar bo'yicha takrorlash holati */
export type CardsSummary = {
  sections: Record<string, { total: number; mastered: number; learning: number; due: number }>;
  due: number;
  new_left: number;
  new_per_day: number;
};
