import { onBeforeUnmount, onMounted } from 'vue';
import { refreshStock } from '@/utils/assistive/api';
import { hasBackend } from '@/utils/assistive/remote';
import type { Stock } from '@/utils/assistive/types';

/**
 * 庫存頁開著時每 10 秒向後端更新一次（頁面在背景時不抓），別人預約完或補貨了這裡會跟著變。
 * 抓不到就保留目前畫面，不打斷使用者；沒有設定後端時庫存是固定快照，不需要輪詢。
 */
export const useAssistiveStockPolling = (
  apply: (stock: Record<string, Stock>) => void,
  ms = 10_000
) => {
  let timer: ReturnType<typeof setInterval> | undefined;
  onMounted(() => {
    if (!hasBackend) return;
    timer = setInterval(async () => {
      if (document.visibilityState !== 'visible') return;
      try {
        apply(await refreshStock());
      } catch {
        /* 保留目前畫面 */
      }
    }, ms);
  });
  onBeforeUnmount(() => clearInterval(timer));
};
