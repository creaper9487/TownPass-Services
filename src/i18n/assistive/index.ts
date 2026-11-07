import { computed, ref } from 'vue';
import * as common from './messages/common';
import * as home from './messages/home';
import * as borrow from './messages/borrow';
import * as assess from './messages/assess';
import * as review from './messages/review';
import * as reservations from './messages/reservations';
import * as welfare from './messages/welfare';
import * as education from './messages/education';
import { dataEn } from './data-en';

/**
 * 輔具預約的雙語（繁體中文／English）。
 * - 介面文字用 t('區.名稱', { 參數 })；沒有英文就退回中文。
 * - 資料值（輔具類別、項目、行政區、中心名稱、是／否）用 tx(中文)；資料本身永遠是中文。
 * - 官方長篇原文沒有英文，英文介面下維持中文並標上 lang="zh-TW"（用 zhAttr）。
 * 語言來源依序：使用者手動選的 → 網址 ?lang= → 瀏覽器語言 → 繁體中文。
 */
export type Lang = 'zh-TW' | 'en';
export const LANGS: { value: Lang; label: string }[] = [
  { value: 'zh-TW', label: '繁體中文' },
  { value: 'en', label: 'English' }
];

const STORAGE_KEY = 'assistive.lang';
const parse = (v?: string | null): Lang | null => {
  const s = v?.toLowerCase();
  if (!s) return null;
  if (s.startsWith('en')) return 'en';
  if (s.startsWith('zh')) return 'zh-TW';
  return null;
};

const detect = (): Lang => {
  try {
    const saved = parse(localStorage.getItem(STORAGE_KEY));
    if (saved) return saved;
  } catch {
    /* 無法讀取儲存空間就略過 */
  }
  const fromUrl = parse(new URLSearchParams(window.location.search).get('lang'));
  if (fromUrl) return fromUrl;
  for (const l of navigator.languages ?? [navigator.language]) {
    const p = parse(l);
    if (p) return p;
  }
  return 'zh-TW';
};

export const lang = ref<Lang>(detect());

const zhMessages: Record<string, string> = {
  ...common.zh,
  ...home.zh,
  ...borrow.zh,
  ...assess.zh,
  ...review.zh,
  ...reservations.zh,
  ...welfare.zh,
  ...education.zh
};
const enMessages: Record<string, string> = {
  ...common.en,
  ...home.en,
  ...borrow.en,
  ...assess.en,
  ...review.en,
  ...reservations.en,
  ...welfare.en,
  ...education.en
};

const warned = new Set<string>();
export const t = (key: string, params?: Record<string, string | number>): string => {
  const text = (lang.value === 'en' ? enMessages[key] : undefined) ?? zhMessages[key];
  if (text === undefined) {
    if (import.meta.env.DEV && !warned.has(key)) {
      warned.add(key);
      console.warn(`[assistive i18n] missing key: ${key}`);
    }
    return key;
  }
  return params
    ? text.replace(/\{(\w+)\}/g, (_, k: string) => String(params[k] ?? `{${k}}`))
    : text;
};

/** 資料值的顯示文字；英文介面下有收錄才翻，否則維持中文 */
export const tx = (zh: string): string => (lang.value === 'en' ? dataEn[zh] ?? zh : zh);

/** 官方中文原文放進英文介面時要加的 lang 屬性（中文介面不用） */
export const zhAttr = computed(() => (lang.value === 'en' ? 'zh-TW' : undefined));

/**
 * 預約摘要一律存中文（也不會送給後端），顯示時才翻：
 * 「申請評估：氣墊床」「助行器・無輪・使用者身高150-175cm」。
 */
export const trSummary = (line: string): string => {
  // 舊紀錄的借用項目是「類別・品名・規格」串成的一行，讀不出哪段是什麼：只顯示品名
  const parts = line.split('・');
  if (parts.length > 1) return parts[1];
  if (lang.value !== 'en') return line;
  const prefixes: Record<string, string> = {
    '申請評估：': 'Assessment: ',
    '申請維修：': 'Repair: ',
    '其他：': 'Other: '
  };
  for (const [zh, en] of Object.entries(prefixes)) {
    if (line.startsWith(zh)) return en + trSummary(line.slice(zh.length));
  }
  return tx(line);
};

export const applyLang = () => {
  document.documentElement.lang = lang.value;
  document.title = t('app.title');
};

export const setLang = (value: Lang) => {
  lang.value = value;
  try {
    localStorage.setItem(STORAGE_KEY, value);
  } catch {
    /* 無法儲存就只在這次有效 */
  }
  applyLang();
};
