export const digits = (value: string) => value.replace(/\D/g, '');

/** 手機：09 開頭共 10 碼（容許空白與連字號） */
export const isMobile = (value: string) => /^09\d{8}$/.test(digits(value));

/** 市話：區碼 + 號碼，共 9–10 碼 */
export const isLandline = (value: string) => /^0[2-8]\d{7,8}$/.test(digits(value));

export const isEmail = (value: string) => /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(value.trim());

const LETTER_CODE: Record<string, number> = {
  A: 10,
  B: 11,
  C: 12,
  D: 13,
  E: 14,
  F: 15,
  G: 16,
  H: 17,
  I: 34,
  J: 18,
  K: 19,
  L: 20,
  M: 21,
  N: 22,
  O: 35,
  P: 23,
  Q: 24,
  R: 25,
  S: 26,
  T: 27,
  U: 28,
  V: 29,
  W: 32,
  X: 30,
  Y: 31,
  Z: 33
};

/** 身分證字號格式與檢查碼（國民身分證與外來人口統一證號） */
export const isTwId = (value: string) => {
  const id = value.trim().toUpperCase();
  if (!/^[A-Z][12ABCD89]\d{8}$/.test(id)) return false;
  const letter = LETTER_CODE[id[0]];
  let second = id[1];
  // 新式外來人口統一證號第二碼為 A–D，取其個位數
  if (/[A-D]/.test(second)) second = String(LETTER_CODE[second] % 10);
  const nums = [
    Math.floor(letter / 10),
    letter % 10,
    ...(second + id.slice(2)).split('').map(Number)
  ];
  const weights = [1, 9, 8, 7, 6, 5, 4, 3, 2, 1, 1];
  const sum = nums.reduce((acc, n, i) => acc + n * weights[i], 0);
  return sum % 10 === 0;
};

/** 從「臺北市中山區…」這類地址抓出臺北市行政區 */
export const districtFromAddress = (address: string) => {
  const m = address
    .replace(/台/g, '臺')
    .match(/臺北市\s*(松山|信義|大安|中山|中正|大同|萬華|文山|南港|內湖|士林|北投)區/);
  return m ? `${m[1]}區` : '';
};

export interface SummaryItem {
  text: string;
  /** 對應欄位的 id，錯誤摘要的連結會跳到這裡 */
  target: string;
}

/** 把 { 欄位: 錯誤訊息 } 轉成錯誤摘要清單（只留有錯誤的欄位） */
export const toSummary = (errors: Record<string, string>, prefix: string): SummaryItem[] =>
  Object.entries(errors)
    .filter(([, message]) => message)
    .map(([key, message]) => ({ text: message, target: `${prefix}-${key}` }));
