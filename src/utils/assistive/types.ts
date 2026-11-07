export type ServiceId = 'borrow' | 'assess';

export interface Center {
  id: 'heyi' | 'south' | 'west';
  name: string;
  shortName: string;
  /** 服務行政區（評估、維修依居住地行政區對應中心） */
  districts: string[];
  address: string;
  addressNote?: string;
  phone: string;
  /** 0 = 週日 … 6 = 週六 */
  openDays: number[];
  hours: { from: string; to: string }[];
  /** 約略座標，僅用於「離我最近」的距離排序 */
  lat: number;
  lng: number;
}

/** 款式的結構化規格（由爬蟲或後端提供；沒有的欄位一律當作「未標示」） */
export interface VariantFit {
  /** 適用身高範圍（公分） */
  heightMin?: number;
  heightMax?: number;
  /** 座寬（吋），可能同時適用多種 */
  seatWidthIn?: number[];
  /** 適用體重範圍（公斤） */
  weightMinKg?: number;
  weightMaxKg?: number;
}

export interface Variant extends VariantFit {
  id: string;
  name: string;
  image: string;
  specs: string[];
  description: string;
  source: string;
}

/** 中心逐日行事曆：含國定假日與臨時休館 */
export interface CalendarDay {
  /** YYYY-MM-DD（臺北） */
  date: string;
  open: boolean;
  /** 休館原因，例如「國定假日」「臨時休館」 */
  reason?: string;
}

/** 某款式在各中心的庫存 */
export type CenterStockMap = Record<string, { stock: number }>;

export interface Category {
  id: string;
  name: string;
  image: string;
  source: string;
  variants: Variant[];
}

export interface Stock {
  stock: number;
  waiting: number;
}

export interface ApplicantForm {
  name: string;
  mobile: string;
  phone: string;
  gender: '' | 'M' | 'F';
  email: string;
}

export interface UserForm {
  name: string;
  idNo: string;
  gender: '' | 'M' | 'F';
  /** 戶籍地行政區（臺北市） */
  registeredDistrict: string;
  /** 居住地行政區（臺北市） */
  livingDistrict: string;
  remark: string;
}

export interface Reservation {
  id: string;
  service: ServiceId;
  createdAt: string;
  /** 與後端相同：booked 已預約、submitted 已送出、confirmed 中心已確認、completed 已完成、cancelled 已取消、expired 已逾期 */
  status: 'booked' | 'submitted' | 'confirmed' | 'completed' | 'cancelled' | 'expired';
  /** 後端回傳的查詢與取消密鑰（只存在這台裝置） */
  accessKey?: string;
  centerId: Center['id'];
  /** 輔具／服務項目摘要 */
  summary: string[];
  /** 借用：款式代碼（顯示照片與規格用；舊紀錄沒有，就用 summary 的文字） */
  itemIds?: string[];
  contactName: string;
  mobile: string;
  /** 借用：取貨期限 (ISO date) */
  pickupDeadline?: string;
  /** 借用：期限內中心實際開館、可以去取貨的日子 (ISO date) */
  pickupDates?: string[];
}
