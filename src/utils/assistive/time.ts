import { onBeforeUnmount, ref } from 'vue';

/**
 * 臺北現在的牆上時間（以本機 Date 表示）。
 * 開館日與取貨期限要以臺北時間判斷，不能依裝置所在時區或被改過的時區。
 */
// 開發用：網址帶 ?mockNow=2026-11-09T10:00:00（或在 sessionStorage 設 assistive.mockNow）就把「臺北現在時間」固定在那一刻，
// 晚上或週末也能測需要開館日的流程。只在開發版有效，正式版不認。
const mockNow = (): Date | null => {
  if (!import.meta.env.DEV) return null;
  try {
    const fromUrl = new URLSearchParams(window.location.search).get('mockNow');
    if (fromUrl) sessionStorage.setItem('assistive.mockNow', fromUrl);
    const raw = sessionStorage.getItem('assistive.mockNow');
    const d = raw ? new Date(raw) : null;
    return d && !Number.isNaN(d.getTime()) ? d : null;
  } catch {
    return null;
  }
};

export const taipeiNow = (): Date => {
  const mocked = mockNow();
  if (mocked) return mocked;
  const parts = new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Asia/Taipei',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hourCycle: 'h23'
  }).formatToParts(new Date());
  const get = (type: string) => Number(parts.find((p) => p.type === type)?.value ?? 0);
  return new Date(
    get('year'),
    get('month') - 1,
    get('day'),
    get('hour'),
    get('minute'),
    get('second')
  );
};

/** 會隨時間更新的臺北現在時間（每 30 秒），頁面停留很久也不會停在過期的開館狀態 */
export const useTaipeiNow = () => {
  const now = ref(taipeiNow());
  const timer = setInterval(() => (now.value = taipeiNow()), 30_000);
  onBeforeUnmount(() => clearInterval(timer));
  return now;
};
