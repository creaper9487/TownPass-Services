/**
 * 後端資料來源。
 * 設定 VITE_ASSISTIVE_API_BASE（例如 https://example.gov.taipei/api/assistive）後才會真的連線；
 * 沒設定、連不上或回傳不是 2xx 時一律回傳 null，畫面會退回目前的行為，不會壞掉。
 */
const BASE = (import.meta.env.VITE_ASSISTIVE_API_BASE as string | undefined)?.replace(/\/$/, '');

export const hasBackend = !!BASE;

/** 開發用：在主控台執行 localStorage.setItem('assistive.sample', '1') 可啟用範例資料，用來檢查畫面 */
export const useSample = () => {
  if (!import.meta.env.DEV) return false;
  try {
    return localStorage.getItem('assistive.sample') === '1';
  } catch {
    return false;
  }
};

export const getJson = async <T>(path: string): Promise<T | null> => {
  if (!BASE) return null;
  try {
    const res = await fetch(`${BASE}${path}`, { headers: { Accept: 'application/json' } });
    return res.ok ? ((await res.json()) as T) : null;
  } catch {
    return null;
  }
};
