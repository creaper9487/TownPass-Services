/**
 * 推播（Firebase Cloud Messaging）登記。
 *
 * 推播 token 只有台北通 App 拿得到：網頁用 push_token 訊息向 App 要，App 會先詢問使用者
 * （沒有同意、系統拒絕通知、或沒有設定 Firebase 時回傳空值），拿到後由網頁用自己的信箱登記給後端。
 * 後端依信箱把預約進度、取貨提醒、到貨消息推播到登記過的手機。
 * 沒有登記成功就不會有推播，畫面與本機通知照常運作。
 */
import { inApp } from '@/composables/useAssistiveNative';
import { useConnectionMessage } from '@/composables/useConnectionMessage';
import { webMailbox, withMailbox } from './api';
import { hasBackend, requestJson } from './remote';

/** 後端的公告主題（service.notice）；App 同意推播後順便訂閱 */
const TOPICS = ['assistive-notice'];
const STORAGE_KEY = 'assistive.push';
/** 使用者在授權視窗與系統通知權限上要花時間，所以等久一點；背景更新（silent）不會跳視窗 */
const ASK_TIMEOUT_MS = 120_000;
const SILENT_TIMEOUT_MS = 4_000;

interface Registered {
  mailboxId: string;
  token: string;
}

const readRegistered = (): Registered | null => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Registered) : null;
  } catch {
    return null;
  }
};
const writeRegistered = (value: Registered | null) => {
  try {
    if (value) localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
    else localStorage.removeItem(STORAGE_KEY);
  } catch {
    /* 儲存空間不能用：下次開啟會再登記一次，後端對同一個 token 重複登記視為更新 */
  }
};

/** 這支手機目前是否已向後端登記推播；已登記時預約進度會由後端推播，網頁就不再自己跳同一則本機通知 */
export const isPushRegistered = () => readRegistered() !== null;

/** 向 App 要 token；沒有同意、逾時或不在 App 內一律回傳 null */
const requestToken = (silent: boolean): Promise<string | null> =>
  new Promise((resolve) => {
    // @ts-ignore flutterObject 由台北通 App 注入
    const bridge = typeof flutterObject !== 'undefined' ? flutterObject : null;
    if (!bridge) return resolve(null);

    const finish = (value: string | null) => {
      clearTimeout(timer);
      bridge.removeEventListener('message', onMessage);
      resolve(value);
    };
    const onMessage = (event: { data: string }) => {
      try {
        const reply = JSON.parse(event.data);
        if (reply?.name !== 'push_token') return;
        const data = reply.data;
        finish(data && !Array.isArray(data) && typeof data.token === 'string' ? data.token : null);
      } catch {
        /* 非 JSON 訊息，略過 */
      }
    };
    const timer = setTimeout(() => finish(null), silent ? SILENT_TIMEOUT_MS : ASK_TIMEOUT_MS);
    bridge.addEventListener('message', onMessage);
    useConnectionMessage('push_token', { silent, topics: TOPICS });
  });

let inFlight: Promise<boolean> | null = null;

/**
 * 讓後端知道要把這個信箱的通知推到這支手機。回傳是否已登記成功。
 * - 預設會由 App 詢問使用者（只問一次，結果記在 App）；silent 只在已同意時更新，不會跳視窗。
 * - 在預約、登記到貨通知「之前」呼叫：後端是在事件發生當下推播，晚登記就收不到那一則。
 * - 任何失敗都回傳 false，不影響預約本身。
 */
export const ensurePush = (options: { silent?: boolean } = {}): Promise<boolean> => {
  if (!hasBackend || !inApp()) return Promise.resolve(false);
  inFlight ??= register(options.silent ?? false).finally(() => (inFlight = null));
  return inFlight;
};

const register = async (silent: boolean): Promise<boolean> => {
  try {
    const token = await requestToken(silent);
    const saved = readRegistered();
    if (!token) {
      // 使用者撤回授權或關掉通知：請後端不要再推播到這支手機
      if (saved) await unregister(saved);
      return false;
    }
    const box = await webMailbox();
    if (saved?.mailboxId === box.id && saved.token === token) return true;
    await withMailbox((b) =>
      requestJson(
        'POST',
        '/devices',
        { mailbox_id: b.id, platform: 'fcm', token },
        { Authorization: `Bearer ${b.key}` }
      )
    );
    writeRegistered({ mailboxId: (await webMailbox()).id, token });
    return true;
  } catch {
    return false;
  }
};

const unregister = async (saved: Registered) => {
  try {
    const box = await webMailbox();
    if (box.id === saved.mailboxId) {
      await requestJson(
        'DELETE',
        `/devices?mailbox_id=${encodeURIComponent(box.id)}`,
        { token: saved.token },
        { Authorization: `Bearer ${box.key}` }
      );
    }
  } catch {
    /* 後端連不上：先清掉這裡的紀錄，推播失敗時後端會自己移除失效的 token */
  }
  writeRegistered(null);
};
