/**
 * 輔具衛教：臺北市輔具資源整合資訊網「輔具衛教」的文章（全文原樣，資料由 scripts/assistive/crawl-education.mjs 抓取）。
 * 內文在資料裡是一行一個字串：空字串 = 段落分隔，「• 」開頭 = 清單項目；這裡把它整理成畫面用的區塊。
 */
import type { RouteLocationRaw } from 'vue-router';
import raw from '@/data/assistive-education.json';
import { catalog } from './catalog';

export interface EducationArticle {
  id: string;
  /** 官網完整標題，例如「【輔具介紹】合宜輔具中心衛教－氣墊床Ⅲ（操作及保養篇）」 */
  title: string;
  /** 標題前綴【…】：輔具介紹、維修保養、宣導影片；沒有前綴就是空字串 */
  category: string;
  /** 去掉前綴的標題 */
  name: string;
  /** 官網寫法：民國110年07月20日 */
  date: string;
  iso: string;
  lines: string[];
  /** YouTube 影片代碼 */
  video?: string;
  source: string;
}

export const articles = raw as EducationArticle[];
export const articleById = (id: string) => articles.find((a) => a.id === id);

/** 分頁籤：官網沒有分類功能，這是依標題前綴分的；沒有前綴的文章只出現在「全部」 */
export const educationCategories = ['輔具介紹', '維修保養', '宣導影片'];

/** 列表卡片的摘要：內文開頭約 90 字 */
export const excerptOf = (a: EducationArticle, max = 90) => {
  const text = a.lines
    .filter(Boolean)
    .map((l) => l.replace(/^• /, ''))
    .join('');
  return text.length > max ? `${text.slice(0, max)}…` : text;
};

export type EducationBlock =
  | { type: 'h'; text: string }
  | { type: 'sub'; text: string }
  | { type: 'p'; text: string }
  | { type: 'step'; label: string; lines: string[] }
  | { type: 'ul'; items: string[] }
  | { type: 'ol'; items: string[] }
  | { type: 'contact'; name: string; phone: string; display: string; address: string };

const CJK = new RegExp('[\\u3000-\\u9fff\\uff00-\\uffef]');
const isCjk = (c?: string) => !!c && CJK.test(c);
/** 原文為了排版在句中換行：中文直接接起來，英數之間補一個空格 */
const join = (parts: string[]) =>
  parts.reduce(
    (acc, p) => (!acc ? p : isCjk(acc.slice(-1)) || isCjk(p[0]) ? acc + p : `${acc} ${p}`),
    ''
  );

const HEADING = /^[一二三四五六七八九十]+、/;
const MARKER = /^＜(.+)＞$/;
const NUMBERED = /^\d+\s*[.、．]\s*/;
const CENTER = /^《(.+)》$/;
const PHONE = /^\((0\d)\)\s*([\d-]+)\s*／?\s*(.*)$/;

export const parseBody = (lines: string[]): EducationBlock[] => {
  const out: EducationBlock[] = [];
  let para: string[] = [];
  let step: Extract<EducationBlock, { type: 'step' }> | null = null;

  const flush = () => {
    if (para.length) out.push({ type: 'p', text: join(para) });
    para = [];
  };
  const pushList = (type: 'ul' | 'ol', item: string) => {
    const last = out[out.length - 1];
    if (last?.type === type) last.items.push(item);
    else out.push({ type, items: [item] });
  };
  /** 往後找下一個非空白行（清單項目之間、中心名稱與電話之間常夾著空行） */
  const nextText = (from: number) => {
    for (let k = from; k < lines.length; k++) if (lines[k]) return k;
    return -1;
  };

  for (let i = 0; i < lines.length; i++) {
    const l = lines[i];
    if (!l) {
      flush();
      step = null;
      continue;
    }
    const marker = l.match(MARKER);
    if (marker) {
      flush();
      step = null;
      if (marker[1].startsWith('步驟')) {
        step = { type: 'step', label: marker[1], lines: [] };
        out.push(step);
      } else {
        out.push({ type: 'sub', text: marker[1] });
      }
      continue;
    }
    if (step) {
      if (HEADING.test(l)) {
        step = null;
      } else {
        step.lines.push(l);
        continue;
      }
    }
    if (HEADING.test(l)) {
      flush();
      out.push({ type: 'h', text: l });
    } else if (l.startsWith('• ')) {
      flush();
      pushList('ul', l.slice(2));
    } else if (NUMBERED.test(l)) {
      flush();
      if (/[：:]$/.test(l)) out.push({ type: 'sub', text: l });
      else pushList('ol', l.replace(NUMBERED, ''));
    } else if (CENTER.test(l)) {
      flush();
      const k = nextText(i + 1);
      const phone = k >= 0 ? lines[k].match(PHONE) : null;
      if (phone) {
        const digits = `${phone[1]}${phone[2].replace(/\D/g, '')}`;
        out.push({
          type: 'contact',
          name: l.match(CENTER)![1],
          phone: digits,
          display: `(${phone[1]})${phone[2]}`,
          address: phone[3]
        });
        i = k;
      } else {
        out.push({ type: 'p', text: l });
      }
    } else {
      para.push(l);
    }
  }
  flush();
  // 清單項目之間的空行已經在 pushList 合併（同類型相鄰就接在一起）；步驟只留有內容的
  return out.filter((b) => b.type !== 'step' || b.lines.length || b.label);
};

export interface EducationRelated {
  /** 對應 education.related.* 的訊息 key */
  key: 'borrow' | 'assess' | 'rules';
  /** borrow 才有：要帶進訊息的輔具類別名稱（中文，畫面用 tx 轉換） */
  category?: string;
  to: RouteLocationRaw;
}

/** 文章對應到可以採取行動的地方：借用該類輔具、預約評估維修、看借用須知 */
const relatedMap: Record<string, { key: EducationRelated['key']; category?: string }> = {
  '78': { key: 'borrow', category: '氣墊床' },
  '77': { key: 'borrow', category: '氣墊床' },
  '74': { key: 'borrow', category: '氣墊床' },
  '59': { key: 'borrow', category: '輪椅' },
  '81': { key: 'borrow', category: '輪椅' },
  '65': { key: 'borrow', category: '輪椅' },
  '3': { key: 'borrow', category: '照顧床' },
  '62': { key: 'assess' },
  '63': { key: 'assess' },
  '64': { key: 'assess' },
  '69': { key: 'assess' },
  '80': { key: 'assess' },
  '82': { key: 'assess' },
  '61': { key: 'rules' }
};

export const relatedOf = (a: EducationArticle): EducationRelated | null => {
  const r = relatedMap[a.id];
  if (!r) return null;
  if (r.key === 'assess') {
    return { key: 'assess', to: { name: 'assistive-need', params: { service: 'assess' } } };
  }
  if (r.key === 'rules') {
    return { key: 'rules', to: { name: 'assistive-rules', params: { service: 'borrow' } } };
  }
  // 分類名稱以後端的目錄為準（官網是「輪椅」，測試資料是「輪椅類」），用關鍵字比對；找不到就不顯示連結
  const category = catalog.value.find((c) => c.name.includes(r.category ?? '\0'));
  return category
    ? {
        key: 'borrow',
        category: category.name.replace(/類$/, ''),
        to: {
          name: 'assistive-variants',
          params: { service: 'borrow', categoryId: category.id }
        }
      }
    : null;
};
