/**
 * 輔具預約資料層。
 *
 * 目前沒有輔具中心系統的 API，這一層用 localStorage 模擬：庫存取自
 * 2026-11-07 抓取的官方快照，預約單存在本機。串接正式系統時只要換掉這個檔案，
 * 頁面與 store 都不用動。
 */
import stockSnapshot from '@/data/assistive-stock.json';
import { formatDate, pickupWindow, centerById } from './centers';
import { taipeiNow } from './time';
import { getJson, hasBackend, useSample } from './remote';
import type {
  CalendarDay,
  Center,
  CenterStockMap,
  RentalStore,
  Reservation,
  ServiceId,
  Stock,
  VariantFit
} from './types';

const STORAGE_KEY = 'assistive.reservations';
const ARRIVAL_KEY = 'assistive.arrival';
const delay = (ms = 350) => new Promise((resolve) => setTimeout(resolve, ms));

const read = <T>(key: string, fallback: T): T => {
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
};
const write = (key: string, value: unknown) => {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* 無痕模式或儲存空間滿了：忽略，本次操作仍可完成 */
  }
};

export const fetchStock = async (): Promise<Record<string, Stock>> => {
  await delay(150);
  // 開發用：在主控台執行 localStorage.setItem('assistive.failStock', '1') 可模擬庫存讀取失敗
  if (import.meta.env.DEV && localStorage.getItem('assistive.failStock') === '1') {
    throw new Error('stock unavailable');
  }
  return stockSnapshot.items as Record<string, Stock>;
};

export interface SubmitPayload {
  service: ServiceId;
  centerId: Center['id'];
  summary: string[];
  contactName: string;
  mobile: string;
  /** 借用：畫面上算出的取貨期限與可前往日期（含行事曆）；沒給就用星期規則 */
  pickup?: { deadline: Date; openDates: Date[] };
}

const prefix: Record<ServiceId, string> = { borrow: 'B', assess: 'A', recycle: 'C' };

export const submitReservation = async (payload: SubmitPayload): Promise<Reservation> => {
  await delay(600);
  const now = new Date();
  const tw = taipeiNow();
  const ymd = `${tw.getFullYear()}${String(tw.getMonth() + 1).padStart(2, '0')}${String(tw.getDate()).padStart(2, '0')}`;
  const reservation: Reservation = {
    id: `${prefix[payload.service]}${ymd}${String(Math.floor(Math.random() * 10000)).padStart(4, '0')}`,
    service: payload.service,
    createdAt: now.toISOString(),
    // 借用為線上預約即成立；評估、維修、回收需待中心回電確認
    status: payload.service === 'borrow' ? 'booked' : 'pending',
    centerId: payload.centerId,
    summary: payload.summary,
    contactName: payload.contactName,
    mobile: payload.mobile
  };
  if (payload.service === 'borrow') {
    const center = centerById(payload.centerId);
    if (center) {
      const win = payload.pickup ?? pickupWindow(center, taipeiNow());
      reservation.pickupDeadline = win.deadline.toISOString();
      reservation.pickupDates = win.openDates.map((d) => d.toISOString());
    }
  }
  write(STORAGE_KEY, [reservation, ...read<Reservation[]>(STORAGE_KEY, [])]);
  return reservation;
};

export const listReservations = async (): Promise<Reservation[]> => {
  await delay(120);
  return read<Reservation[]>(STORAGE_KEY, []);
};

export const cancelReservation = async (id: string): Promise<void> => {
  await delay(400);
  write(
    STORAGE_KEY,
    read<Reservation[]>(STORAGE_KEY, []).map((r) =>
      r.id === id ? { ...r, status: 'cancelled' as const } : r
    )
  );
};

export const arrivalSubscriptions = () => read<string[]>(ARRIVAL_KEY, []);

export const subscribeArrival = async (typeId: string): Promise<void> => {
  await delay(300);
  const list = new Set(arrivalSubscriptions());
  list.add(typeId);
  write(ARRIVAL_KEY, [...list]);
};

export const unsubscribeArrival = async (typeId: string): Promise<void> => {
  await delay(300);
  write(
    ARRIVAL_KEY,
    arrivalSubscriptions().filter((id) => id !== typeId)
  );
};

export const deadlineText = (r: Reservation) =>
  r.pickupDeadline ? formatDate(new Date(r.pickupDeadline)) : '';

/** 期限內可以去取貨的日子，例如「11/7（週六）」 */
export const pickupDatesText = (r: Reservation) =>
  (r.pickupDates ?? []).map((d) => formatDate(new Date(d))).join('、');

export type EffectiveStatus = Reservation['status'] | 'expired';

/**
 * 實際要顯示的狀態。官方規則：借用預約逾取貨期限會自動取消。
 * 這裡依臺北時間判斷，讓使用者在「我的預約」就看得到，而不是靠一則不會寄來的通知。
 */
export const effectiveStatus = (r: Reservation, now = taipeiNow()): EffectiveStatus => {
  if (r.status === 'booked' && r.pickupDeadline) {
    const d = new Date(r.pickupDeadline);
    const endOfDeadlineDay = new Date(d.getFullYear(), d.getMonth(), d.getDate() + 1);
    if (now >= endOfDeadlineDay) return 'expired';
  }
  return r.status;
};

export const statusText = (r: Reservation) => {
  switch (effectiveStatus(r)) {
    case 'cancelled':
      return '已取消';
    case 'expired':
      return '已逾期，預約已自動取消';
    case 'booked':
      return '已預約，待取貨';
    default:
      return '已送出，等中心回電';
  }
};

/**
 * 以下四個函式是給後端資料準備的轉接層：有資料就回傳，沒有（沒設定後端、連不上、尚未提供）就回傳 null，
 * 呼叫端要自己退回目前的行為。
 */

/** 附近的民間租賃特約門市。GET /rental-stores?category={id} */
export const fetchRentalStores = async (categoryId: string): Promise<RentalStore[] | null> => {
  if (import.meta.env.DEV && useSample())
    return (await import('./sample')).sampleRentalStores(categoryId);
  const data = await getJson<{ stores: RentalStore[] }>(
    `/rental-stores?category=${encodeURIComponent(categoryId)}`
  );
  return data?.stores?.length ? data.stores : null;
};

/** 中心逐日行事曆。GET /centers/{id}/calendar?from=&to= */
export const fetchCenterCalendar = async (
  centerId: string,
  from: string,
  to: string
): Promise<CalendarDay[] | null> => {
  if (import.meta.env.DEV && useSample())
    return (await import('./sample')).sampleCalendar(centerId, taipeiNow());
  const data = await getJson<{ days: CalendarDay[] }>(
    `/centers/${encodeURIComponent(centerId)}/calendar?from=${from}&to=${to}`
  );
  return data?.days?.length ? data.days : null;
};

/** 某款式在各中心的庫存。GET /stock/{variantId}/centers（注意：不可用分類總庫存代替） */
export const fetchCenterStock = async (variantId: string): Promise<CenterStockMap | null> => {
  if (import.meta.env.DEV && useSample()) return (await import('./sample')).sampleCenterStock();
  return getJson<CenterStockMap>(`/stock/${encodeURIComponent(variantId)}/centers`);
};

/** 款式的結構化規格（身高、座寬、體重）。GET /variants/specs */
export const fetchVariantFits = async (): Promise<Record<string, VariantFit> | null> => {
  if (import.meta.env.DEV && useSample()) return (await import('./sample')).sampleVariantFit;
  return getJson<Record<string, VariantFit>>('/variants/specs');
};

export { hasBackend };
