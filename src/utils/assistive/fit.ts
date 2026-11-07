import type { Variant, VariantFit } from './types';

const num = (v: string) => Number(v);

/**
 * 從現有的自由文字規格（specs）讀出身高、體重、座寬。
 * 只認官方文字裡明確的幾種寫法；讀不出來的就留空，該款式會被當成「未標示」一律列出。
 * 爬蟲或後端提供結構欄位後，以他們的資料為準（見 mergeFit）。
 */
export const deriveFit = (v: Pick<Variant, 'specs'>): VariantFit => {
  const text = v.specs.join(' ');
  const fit: VariantFit = {};

  const hRange = text.match(/身高\s*(\d{2,3})\s*[-–~]\s*(\d{2,3})\s*cm/i);
  const hMin = text.match(/身高\s*(\d{2,3})\s*cm\s*以上/i);
  const hMax = text.match(/身高\s*(\d{2,3})\s*cm\s*以下/i);
  if (hRange) {
    fit.heightMin = num(hRange[1]);
    fit.heightMax = num(hRange[2]);
  } else if (hMin) fit.heightMin = num(hMin[1]);
  else if (hMax) fit.heightMax = num(hMax[1]);

  const wRange = text.match(/體重\s*(\d{2,3})\s*[-–~]\s*(\d{2,3})\s*公斤/);
  const wMax = text.match(/體重\s*(\d{2,3})\s*公斤\s*以下/);
  if (wRange) {
    fit.weightMinKg = num(wRange[1]);
    fit.weightMaxKg = num(wRange[2]);
  } else if (wMax) fit.weightMaxKg = num(wMax[1]);

  const seat =
    text.match(/座寬\s*(\d{2})\s*或\s*(\d{2})\s*吋/) ?? text.match(/座寬\s*(\d{2})\s*吋/);
  if (seat) fit.seatWidthIn = seat.slice(1).filter(Boolean).map(num);

  return fit;
};

const KEYS: (keyof VariantFit)[] = [
  'heightMin',
  'heightMax',
  'seatWidthIn',
  'weightMinKg',
  'weightMaxKg'
];

/** 以遠端（爬蟲或後端）提供的結構欄位為主，缺的欄位用文字推出來的補 */
export const mergeFit = (v: Variant, remote?: VariantFit | null): VariantFit => {
  const merged: VariantFit = { ...deriveFit(v) };
  for (const source of [v, remote ?? {}] as VariantFit[]) {
    for (const k of KEYS) {
      if (source[k] !== undefined) (merged as Record<string, unknown>)[k] = source[k];
    }
  }
  return merged;
};

export const hasHeight = (f: VariantFit) => f.heightMin !== undefined || f.heightMax !== undefined;
export const hasWeight = (f: VariantFit) =>
  f.weightMinKg !== undefined || f.weightMaxKg !== undefined;

export type FitMatch = 'yes' | 'no' | 'unknown';

/**
 * 依使用者輸入的身高、體重判斷款式是否適用。
 * 只比對「使用者有輸入、而且款式有標示」的項目；任何一項超出範圍就是 no，
 * 沒有任何可比對的項目就是 unknown（沒標示，仍然列出）。
 */
export const matchFit = (f: VariantFit, heightCm?: number, weightKg?: number): FitMatch => {
  let checked = 0;
  if (heightCm !== undefined && hasHeight(f)) {
    checked += 1;
    if (f.heightMin !== undefined && heightCm < f.heightMin) return 'no';
    if (f.heightMax !== undefined && heightCm > f.heightMax) return 'no';
  }
  if (weightKg !== undefined && hasWeight(f)) {
    checked += 1;
    if (f.weightMinKg !== undefined && weightKg < f.weightMinKg) return 'no';
    if (f.weightMaxKg !== undefined && weightKg > f.weightMaxKg) return 'no';
  }
  return checked ? 'yes' : 'unknown';
};

export const HEIGHT_RANGE = { min: 100, max: 230 };
export const WEIGHT_RANGE = { min: 20, max: 250 };
