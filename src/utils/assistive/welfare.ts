import data from '@/data/assistive-welfare.json';

/**
 * 輔具福利查詢：照官方問答的題目與跳題規則（2026-11-07 取自官方網站）。
 * 下一題由「這題的答案、第 1 題輸入的年齡、前面題目的答案」決定。
 */
export interface WelfareRule {
  when: {
    answer?: string;
    age?: { min: number | null; max: number | null };
    answers?: Record<string, string>;
  };
  next: string;
}

export interface WelfareQuestion {
  text: string;
  type: 'number' | 'radio';
  image?: string | null;
  options: { value: string; label: string }[];
  rules: WelfareRule[];
}

export type WelfareBlock = {
  type: 'h' | 'p' | 'li' | 'link';
  text: string;
  href?: string;
  ordered?: boolean;
};

export const welfare = data as unknown as {
  intro: { title: string; text: string; button: string };
  questions: Record<string, WelfareQuestion>;
  result: {
    title: string;
    text: string;
    items: { title: string; page?: string; href?: string }[];
  };
  pages: Record<string, { title: string; blocks: WelfareBlock[] }>;
};

export const FIRST_QUESTION = '1';
export const RESULT = 'result';
export const OFFICIAL_SITE = 'https://tpap.gov.taipei';

const matches = (rule: WelfareRule, qid: string, answers: Record<string, string>, age: number) => {
  const w = rule.when;
  if (w.answer !== undefined && w.answer !== answers[qid]) return false;
  if (w.age) {
    if (w.age.min !== null && age < w.age.min) return false;
    if (w.age.max !== null && age > w.age.max) return false;
  }
  return Object.entries(w.answers ?? {}).every(([k, v]) => answers[k] === v);
};

/**
 * 回答這題之後要去哪裡：下一題的編號，或 'result'。
 * 官方網站在「領有手冊、住屋題答否」時會直接出現系統錯誤（HTTP 500），
 * 這裡讓它照其他答案一樣繼續到第 9 題。
 */
export const nextQuestion = (qid: string, answers: Record<string, string>, age: number) => {
  const rule = welfare.questions[qid].rules.find((r) => matches(r, qid, answers, age));
  const next = rule?.next ?? RESULT;
  return next === 'ERROR_500' ? '9' : next;
};

/** 官方的檢查：Q1 要輸入大於等於 0 的數字 */
export const checkAge = (raw: string) => {
  const text = raw.trim();
  if (text === '' || Number.isNaN(Number(text))) return '請輸入數字!';
  if (Number(text) < 0) return '請輸入大於0的數字!';
  return '';
};
