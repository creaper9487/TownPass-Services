/**
 * 推播（Firebase Cloud Messaging）登記。
 *
 * 信箱金鑰與推播 token 都只在台北通 App 裡：網頁送 assistive_push 訊息，App 會先詢問使用者
 * （沒有同意、系統拒絕通知、沒有設定 Firebase 時回傳 false），同意後由 App 向後端登記這支手機。
 * 沒有登記成功就不會有推播，畫面照常運作（預約成功、取消這類使用者自己剛做的事用畫面與彈窗告知，不靠通知）。
 */
import { inApp } from '@/composables/useAssistiveNative';
import { askApp } from './appBridge';
import { hasBackend } from './remote';

/** 使用者要在授權視窗與系統通知權限上花時間，所以等久一點；背景更新（silent）不會跳視窗 */
const ASK_TIMEOUT_MS = 120_000;
const SILENT_TIMEOUT_MS = 8_000;

let inFlight: Promise<boolean> | null = null;

/**
 * 讓後端知道要把這個信箱的通知推到這支手機。回傳是否已登記成功。
 * - 預設會由 App 詢問使用者（只問一次，結果記在 App）；silent 只在已同意時更新，不會跳視窗。
 * - 在預約、登記到貨通知「之前」呼叫：後端是在事件發生當下推播，晚登記就收不到那一則。
 * - 任何失敗都回傳 false，不影響預約本身。
 */
export const ensurePush = (options: { silent?: boolean } = {}): Promise<boolean> => {
  if (!hasBackend || !inApp()) return Promise.resolve(false);
  const silent = options.silent ?? false;
  inFlight ??= askApp<boolean>(
    'assistive_push',
    { silent },
    silent ? SILENT_TIMEOUT_MS : ASK_TIMEOUT_MS
  )
    .then((registered) => registered === true)
    .finally(() => (inFlight = null));
  return inFlight;
};
