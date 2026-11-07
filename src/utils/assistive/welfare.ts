import data from '@/data/assistive-welfare.json';
import { t } from '@/i18n/assistive';

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

export type WelfareItem = { title: string; page?: string; href?: string };

export const welfare = data as unknown as {
  intro: { title: string; text: string; button: string };
  questions: Record<string, WelfareQuestion>;
  result: {
    title: string;
    text: string;
    /** 依官方結果頁的固定順序排列 */
    items: WelfareItem[];
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

/** 是非題的答案值（官方表單 answer=1 為「是」、2 為「否」） */
const YES = '1';
const NO = '2';

/**
 * 各補助項目在哪些答案下列入結果，2026-11-07 走過官方問答 34 條路徑整理而成。
 * 官方結果頁每次都列出全部 13 項，「是否符合」欄一律顯示「不符合」，
 * 但會把該次答案符合的項目排在最前面，其餘依固定順序接在後面；這裡只保留排在前面的項目。
 * 題號：1 年齡、2 手冊或證明、3 聽覺、4 聲音或語言、5 職業災害、6 就業、7 就學、8 住屋、9 居住臺北市。
 * 住屋題只有 0 歲或 65 歲以上會問到，所以 1～64 歲不會出現住屋相關項目（官方如此）。
 */
const ELIGIBLE: Record<string, (a: Record<string, string>, age: number) => boolean> = {
  // 官方：未領手冊且 65 歲以上的路徑都有；0 歲另以送出就學答案的請求確認；1～64 歲沒有
  身障證明申請: (a, age) => a['2'] === NO && (age === 0 || age >= 65),
  // 官方：65 歲以上且住屋題答「是」（有無手冊皆同）；住屋答「否」、0 歲時沒有
  失能者生活輔助器具補助與無障礙環境改善補助: (a, age) => age >= 65 && a['8'] === YES,
  // 官方：職業災害題答「是」
  職災器具補助: (a) => a['5'] === YES,
  // 官方：就學題答「是」（各年齡皆同，含 65 歲以上）
  特殊教育的輔具服務: (a) => a['7'] === YES,
  // 官方：聽覺題答「是」
  人工電子耳及耗材補助: (a) => a['3'] === YES,
  // 官方：聽覺題或聲音語言題任一答「是」
  手語翻譯服務: (a) => a['3'] === YES || a['4'] === YES,
  // 官方：就業題答「是」
  身障者職務再設計: (a) => a['6'] === YES,
  // 推論：官方「領有手冊、住屋答否」為系統錯誤無結果，依項目名稱（不含限居家）列入
  '身心障礙者醫療費用及醫療輔具補助服務(不含限居家照顧使用輔具)': (a) =>
    a['2'] === YES && a['8'] === NO,
  // 官方：領有手冊且住屋題答「是」（居住臺北市答是或否皆同）
  居家身障者維生器材及必要生活輔具用電優惠: (a) => a['2'] === YES && a['8'] === YES,
  // 官方：領有手冊、住屋答「是」、居住臺北市答「否」
  '身障輔具補助(不含居家環境改善)': (a) => a['2'] === YES && a['8'] === YES && a['9'] === NO,
  // 官方：領有手冊、住屋答「是」、居住臺北市答「是」
  '身障輔具補助(含居家環境改善)': (a) => a['2'] === YES && a['8'] === YES && a['9'] === YES,
  // 推論：同上「領有手冊、住屋答否」的系統錯誤路徑，依項目名稱（不含居家環境改善、不含限居家）列入
  '身障輔具補助(不含居家環境改善、不含限居家使用輔具)': (a) => a['2'] === YES && a['8'] === NO,
  // 官方：領有手冊且住屋題答「是」（居住臺北市答是或否皆同）
  身心障礙者醫療費用及醫療輔具補助服務: (a) => a['2'] === YES && a['8'] === YES
};

/** 依答案列出可能符合的補助項目，順序與官方結果頁相同；可能一項都沒有。表中沒有條件的項目一律列出。 */
export const eligibleItems = (answers: Record<string, string>, age: number): WelfareItem[] =>
  welfare.result.items.filter((item) => ELIGIBLE[item.title]?.(answers, age) ?? true);

/** 官方的檢查：Q1 要輸入大於等於 0 的數字 */
export const checkAge = (raw: string) => {
  const text = raw.trim();
  if (text === '' || Number.isNaN(Number(text))) return t('welfare.error.number');
  if (Number(text) < 0) return t('welfare.error.positive');
  return '';
};
