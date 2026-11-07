/**
 * 輔具目錄（分類與款式）。
 *
 * 後端的 GET /catalog 是唯一的資料來源：款式 id 就是全部 API 用的 variant_id（測試模式的假資料 id 也和官網不同）。
 * 後端連不上時用隨附的官網快照，畫面照常運作；載入成功後整個畫面跟著換成後端的目錄。
 */
import { ref } from 'vue';
import snapshot from '@/data/assistive-catalog.json';
import { getJson } from './remote';
import type { Category } from './types';

export const catalog = ref<Category[]>(snapshot as unknown as Category[]);

let loading: Promise<void> | null = null;

/** 向後端取得目錄（整個服務只取一次）；沒有後端或連不上就維持快照 */
export const loadCatalog = (): Promise<void> => {
  loading ??= (async () => {
    const data = await getJson<{ categories?: Category[] }>('/catalog');
    if (data?.categories?.length) catalog.value = data.categories;
  })();
  return loading;
};
