/**
 * 向台北通 App 要資料並等它回覆（Promise 版的 flutterObject 訊息）。
 *
 * App 的回覆只靠訊息名稱對應，所以同名的訊息一次只送一個、排隊處理；
 * 不在 App 內、App 沒有回覆（逾時）都回傳 null。
 */
import { inApp } from '@/composables/useAssistiveNative';
import { useConnectionMessage } from '@/composables/useConnectionMessage';

const queues = new Map<string, Promise<unknown>>();

const exchange = <T>(name: string, data: unknown, timeoutMs: number): Promise<T | null> =>
  new Promise((resolve) => {
    // @ts-ignore flutterObject 由台北通 App 注入
    const bridge = typeof flutterObject !== 'undefined' ? flutterObject : null;
    if (!bridge) return resolve(null);

    const finish = (value: T | null) => {
      clearTimeout(timer);
      bridge.removeEventListener('message', onMessage);
      resolve(value);
    };
    const onMessage = (event: { data: string }) => {
      try {
        const reply = JSON.parse(event.data);
        if (reply?.name === name) finish((reply.data ?? null) as T | null);
      } catch {
        /* 非 JSON 訊息，略過 */
      }
    };
    const timer = setTimeout(() => finish(null), timeoutMs);
    bridge.addEventListener('message', onMessage);
    useConnectionMessage(name, data);
  });

/** 送訊息給 App 並等回覆；等待時間要夠使用者回應授權視窗時，把 timeoutMs 設長一點 */
export const askApp = <T>(
  name: string,
  data: unknown = null,
  timeoutMs = 20_000
): Promise<T | null> => {
  if (!inApp()) return Promise.resolve(null);
  const previous = queues.get(name) ?? Promise.resolve();
  const next = previous.then(() => exchange<T>(name, data, timeoutMs));
  queues.set(
    name,
    next.catch(() => null)
  );
  return next;
};
