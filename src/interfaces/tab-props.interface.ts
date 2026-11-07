export interface TabsProps {
  tabList?: {
    id: number | string;
    title: string;
    /** 讀屏用的完整名稱（標題帶了數字或符號時用） */
    label?: string;
  }[];
  contentType?: boolean;
  /** 傳入後，分頁會有 id、並以 aria-controls 連到 `${idPrefix}-panel` */
  idPrefix?: string;
  /** tablist 的名稱 */
  listLabel?: string;
}
