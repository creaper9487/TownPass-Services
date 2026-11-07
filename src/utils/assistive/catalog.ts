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

/** 畫面上顯示一件輔具需要的資料：照片、品名、分類、規格（各自一項，不再串成一行） */
export interface VariantInfo {
  id: string;
  name: string;
  category: string;
  image?: string | null;
  specs: string[];
}

const cleanSpecs = (specs: string[], name: string) =>
  specs.filter((s) => s && s !== '---' && s !== '--' && s !== name);

/** 依款式代碼從目錄查出要顯示的資料；目錄裡找不到（例如目錄改版）就回傳 undefined，由呼叫端退回文字 */
export const variantInfo = (id: string): VariantInfo | undefined => {
  for (const c of catalog.value) {
    const v = c.variants.find((x) => x.id === id);
    if (v)
      return {
        id,
        name: v.name,
        category: c.name,
        image: v.image,
        specs: cleanSpecs(v.specs, v.name)
      };
  }
  return undefined;
};

/** 已選進預約的款式（儲存的資料）轉成顯示用；優先用目錄的最新資料，目錄裡沒有就用當時存下來的 */
export const selectedInfo = (v: {
  id: string;
  name: string;
  categoryName: string;
  spec: string;
  image?: string;
}): VariantInfo =>
  variantInfo(v.id) ?? {
    id: v.id,
    name: v.name,
    category: v.categoryName,
    image: v.image,
    specs: v.spec ? v.spec.split('、') : []
  };
