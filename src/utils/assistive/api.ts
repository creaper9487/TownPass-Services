/**
 * 輔具預約資料層。
 *
 * 有設定 VITE_ASSISTIVE_API_BASE 時走後端（Taipei Codefest 2026 Backend，/assistive/v1）：
 * 預約、取消、查詢狀態一律以後端為準，失敗就讓使用者知道，不假裝成功。
 * 後端還沒提供的資料（庫存、行事曆）退回 2026-11-07 的官方庫存快照與依星期判斷。
 * 沒設定後端時整層用 localStorage 模擬，方便單獨開發畫面。
 */
import stockSnapshot from '@/data/assistive-stock.json';
import { formatDate, pickupWindow, centerById } from './centers';
import { taipeiNow } from './time';
import { lang, t } from '@/i18n/assistive';
import { inApp } from '@/composables/useAssistiveNative';
import { askApp } from './appBridge';
import { catalog } from './catalog';
import { ApiError, getJson, hasBackend, requestJson, useSample } from './remote';
import type {
  ApplicantForm,
  CalendarDay,
  Center,
  CenterStockMap,
  Reservation,
  ServiceId,
  Stock,
  UserForm,
  VariantFit
} from './types';

const STORAGE_KEY = 'assistive.reservations';
const MAILBOX_KEY = 'assistive.mailbox';
const ARRIVALS_KEY = 'assistive.arrivals';
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
  // 開發用：在主控台執行 localStorage.setItem('assistive.failStock', '1') 可模擬庫存讀取失敗
  if (import.meta.env.DEV && localStorage.getItem('assistive.failStock') === '1') {
    throw new Error('stock unavailable');
  }
  // GET /stock → { version, as_of, items: { [variantId]: { stock, waiting } } }；後端還沒有資料時退回快照
  const data = await getJson<{ items?: Record<string, { stock?: number; waiting?: number }> }>(
    '/stock'
  );
  if (data?.items && Object.keys(data.items).length) {
    return Object.fromEntries(
      Object.entries(data.items).map(([id, v]) => [
        id,
        { stock: Number(v.stock ?? 0), waiting: Number(v.waiting ?? 0) }
      ])
    );
  }
  await delay(150);
  return stockSnapshot.items as Record<string, Stock>;
};

/** 每種服務送給後端的一筆預約。評估與維修在同一張表單，勾了兩邊就會分成兩筆。 */
export interface SubmitRequest {
  backendService: 'borrow' | 'assess' | 'repair';
  items: string[];
  otherText?: string;
  /** 畫面上顯示的摘要 */
  summary: string[];
}

export interface SubmitPayload {
  service: ServiceId;
  centerId: Center['id'];
  requests: SubmitRequest[];
  contact: ApplicantForm;
  /** 評估、維修才有 */
  subject?: UserForm;
  /** 借用：畫面上算出的取貨期限與可前往日期（含行事曆）；沒給就用星期規則 */
  pickup?: { deadline: Date; openDates: Date[] };
  /** 同一次送出重試時要用同一把，後端才不會重複建立 */
  idempotencyKey: string;
}

export const newIdempotencyKey = () =>
  (typeof crypto !== 'undefined' && 'randomUUID' in crypto ? crypto.randomUUID() : '') ||
  `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 12)}`;

const prefix: Record<ServiceId, string> = { borrow: 'B', assess: 'A' };

const dayToIso = (ymd: string) => {
  const [y, m, d] = ymd.split('-').map(Number);
  return new Date(y, m - 1, d).toISOString();
};

/** 信箱由網頁建立；金鑰只存在這個裝置的瀏覽器儲存空間 */
export const webMailbox = async (): Promise<{ id: string; key: string }> => {
  const saved = read<{ id: string; key: string } | null>(MAILBOX_KEY, null);
  if (saved?.id && saved.key) return saved;
  const box = await requestJson<{ mailbox_id: string; mailbox_key: string }>('POST', '/mailboxes');
  const created = { id: box.mailbox_id, key: box.mailbox_key };
  write(MAILBOX_KEY, created);
  return created;
};

/**
 * 用信箱執行一個請求。後端不認得存在這台裝置上的信箱（後端資料被清掉、換了環境）時，
 * 建立新的信箱再試一次；不然使用者會一直卡在「送出失敗」，只能自己清除瀏覽器資料。
 */
export const withMailbox = async <T>(
  run: (box: { id: string; key: string }) => Promise<T>
): Promise<T> => {
  try {
    return await run(await webMailbox());
  } catch (e) {
    const unknownMailbox =
      e instanceof ApiError &&
      ((e.status === 422 && e.fields.includes('mailbox_id')) ||
        (e.status === 401 && e.code === 'BAD_KEY'));
    if (!unknownMailbox) throw e;
    try {
      localStorage.removeItem(MAILBOX_KEY);
    } catch {
      /* 儲存空間不能用：webMailbox 會直接再建一個 */
    }
    return run(await webMailbox());
  }
};

const isUnknownMailbox = (e: unknown) =>
  e instanceof ApiError &&
  ((e.status === 422 && e.fields.includes('mailbox_id')) ||
    (e.status === 401 && e.code === 'BAD_KEY'));

let appMailbox: string | null = null;

/** 在台北通 App 內，信箱與金鑰由 App 保管，網頁只拿到信箱 id；renew 是後端不認得舊信箱時請 App 換新的 */
const appMailboxId = async (renew = false): Promise<string> => {
  if (!renew && appMailbox) return appMailbox;
  const reply = await askApp<{ mailbox_id?: string }>(
    'assistive_mailbox',
    renew ? { renew: true } : null
  );
  if (!reply || Array.isArray(reply) || typeof reply.mailbox_id !== 'string') {
    throw new Error('mailbox unavailable');
  }
  return (appMailbox = reply.mailbox_id);
};

/** 只需要信箱 id 的請求（預約）：App 內由 App 提供信箱；瀏覽器開發時用網頁自己的信箱。信箱失效時換新的再試一次 */
const withMailboxId = async <T>(run: (mailboxId: string) => Promise<T>): Promise<T> => {
  if (!inApp()) return withMailbox((box) => run(box.id));
  try {
    return await run(await appMailboxId());
  } catch (e) {
    if (!isUnknownMailbox(e)) throw e;
    return run(await appMailboxId(true));
  }
};

interface ReservationCreatedDto {
  id: string;
  access_key: string;
  status: Reservation['status'];
  pickup?: { deadline: string; open_dates: string[] } | null;
}

const submitToBackend = async (payload: SubmitPayload): Promise<Reservation[]> => {
  const c = payload.contact;
  const contact = {
    name: c.name.trim(),
    mobile: c.mobile.trim(),
    phone: c.phone.trim() || null,
    gender: c.gender === 'M' || c.gender === 'F' ? c.gender : 'X',
    email: c.email.trim() || null
  };
  const u = payload.subject;
  const subject = u
    ? {
        name: u.name.trim(),
        id_no: u.idNo.trim().toUpperCase(),
        registered_district: u.registeredDistrict,
        living_county: '臺北市',
        living_district: u.livingDistrict || u.registeredDistrict,
        remark: u.remark.trim() || null
      }
    : null;

  const created: Reservation[] = [];
  for (const r of payload.requests) {
    const res = await withMailboxId((mailboxId) =>
      requestJson<ReservationCreatedDto>(
        'POST',
        '/reservations',
        {
          service: r.backendService,
          mailbox_id: mailboxId,
          center_id: payload.centerId,
          items: r.items,
          other_text: r.otherText || null,
          contact,
          subject: r.backendService === 'borrow' ? null : subject,
          pickup: null
        },
        // 換信箱重送時內容不同，要用另一把 Idempotency-Key，否則後端會回 409
        { 'Idempotency-Key': `${payload.idempotencyKey}-${r.backendService}-${mailboxId}` }
      )
    );
    const reservation: Reservation = {
      id: res.id,
      service: payload.service,
      createdAt: new Date().toISOString(),
      status: res.status,
      accessKey: res.access_key,
      centerId: payload.centerId,
      summary: r.summary,
      contactName: c.name,
      mobile: c.mobile
    };
    if (res.pickup) {
      reservation.pickupDeadline = dayToIso(res.pickup.deadline);
      reservation.pickupDates = res.pickup.open_dates.map(dayToIso);
    }
    // 每建立一筆就先存起來：第二筆失敗時，第一筆不會從清單消失。
    write(STORAGE_KEY, [reservation, ...read<Reservation[]>(STORAGE_KEY, [])]);
    created.push(reservation);
  }
  return created;
};

const submitLocally = async (payload: SubmitPayload): Promise<Reservation[]> => {
  await delay(600);
  const now = new Date();
  const tw = taipeiNow();
  const ymd = `${tw.getFullYear()}${String(tw.getMonth() + 1).padStart(2, '0')}${String(tw.getDate()).padStart(2, '0')}`;
  const list = payload.requests.map((r): Reservation => {
    const reservation: Reservation = {
      id: `${prefix[payload.service]}${ymd}${String(Math.floor(Math.random() * 10000)).padStart(4, '0')}`,
      service: payload.service,
      createdAt: now.toISOString(),
      // 借用為線上預約即成立；評估、維修需待中心回電確認
      status: payload.service === 'borrow' ? 'booked' : 'submitted',
      centerId: payload.centerId,
      summary: r.summary,
      contactName: payload.contact.name,
      mobile: payload.contact.mobile
    };
    if (payload.service === 'borrow') {
      const center = centerById(payload.centerId);
      if (center) {
        const win = payload.pickup ?? pickupWindow(center, taipeiNow());
        reservation.pickupDeadline = win.deadline.toISOString();
        reservation.pickupDates = win.openDates.map((d) => d.toISOString());
      }
    }
    return reservation;
  });
  write(STORAGE_KEY, [...list, ...read<Reservation[]>(STORAGE_KEY, [])]);
  return list;
};

/** 送出預約；回傳實際建立的預約單（評估＋維修同時勾選時會有兩筆） */
export const submitReservation = (payload: SubmitPayload): Promise<Reservation[]> =>
  hasBackend ? submitToBackend(payload) : submitLocally(payload);

interface ReservationStatusDto {
  id: string;
  status: Reservation['status'];
  version: number;
  pickup?: { deadline: string; open_dates: string[] } | null;
  error?: string;
}

export const listReservations = async (): Promise<Reservation[]> => {
  const local = read<Reservation[]>(STORAGE_KEY, []);
  const keyed = local.filter((r) => r.accessKey);
  if (!hasBackend || !keyed.length) {
    await delay(120);
    return local;
  }
  // 依密鑰向後端更新每一筆的最新狀態；連不上時先顯示這台裝置上記得的內容。
  try {
    const res = await requestJson<ReservationStatusDto[]>(
      'POST',
      '/reservations:batchGet',
      keyed.map((r) => ({ id: r.id, access_key: r.accessKey }))
    );
    const byId = new Map(res.map((x) => [x.id, x]));
    const merged = local.map((r) => {
      const x = byId.get(r.id);
      if (!x || x.error) return r;
      return {
        ...r,
        status: x.status,
        pickupDeadline: x.pickup ? dayToIso(x.pickup.deadline) : r.pickupDeadline,
        pickupDates: x.pickup ? x.pickup.open_dates.map(dayToIso) : r.pickupDates
      };
    });
    write(STORAGE_KEY, merged);
    return merged;
  } catch {
    return local;
  }
};

export const cancelReservation = async (id: string): Promise<void> => {
  const local = read<Reservation[]>(STORAGE_KEY, []);
  const target = local.find((r) => r.id === id);
  if (hasBackend && target?.accessKey) {
    // 失敗要讓畫面知道（丟出錯誤），不能顯示成已取消
    await requestJson('POST', `/reservations/${encodeURIComponent(id)}:cancel`, {
      access_key: target.accessKey
    });
  } else {
    await delay(400);
  }
  write(
    STORAGE_KEY,
    local.map((r) => (r.id === id ? { ...r, status: 'cancelled' as const } : r))
  );
};

export interface ArrivalNotice {
  variantId: string;
  /** 畫面上顯示的輔具名稱 */
  label: string;
  /** 登記編號（後端的 subscription id） */
  id: string;
  createdAt: string;
  /** waiting 等待中、arrived 已到貨；沒有後端時只有 waiting */
  status?: 'waiting' | 'arrived';
  /** 品項所屬分類：到貨後回到該分類的款式頁預約 */
  categoryId?: string;
}

/** 到貨通知失敗的原因：後端錯誤碼（DUPLICATE_WAITLIST 同一類已經有等待中的、INVALID_FIELD 品項不存在…）或 NETWORK */
export class ArrivalError extends Error {
  constructor(readonly code: string) {
    super(code);
  }
}

interface SubscriptionDto {
  id: string;
  variant_id: string;
  category_id?: string | null;
  status: 'waiting' | 'arrived';
  created_at?: string | null;
}

/** 這台裝置記得的到貨通知（也是顯示名稱的來源：後端只回品項代碼） */
export const listArrivals = (): ArrivalNotice[] => read<ArrivalNotice[]>(ARRIVALS_KEY, []);

/** 品項代碼對應的顯示名稱，和到貨通知確認頁用同一個寫法 */
export const arrivalLabel = (variantId: string): string | undefined => {
  for (const c of catalog.value) {
    const v = c.variants.find((x) => x.id === variantId);
    if (v) {
      const specs = v.specs.filter((x) => x && x !== '---' && x !== '--' && x !== v.name);
      return [c.name, v.name, ...specs].join('・');
    }
  }
  return undefined;
};

const toNotice = (s: SubscriptionDto, cached?: ArrivalNotice): ArrivalNotice => ({
  variantId: s.variant_id,
  id: s.id,
  status: s.status,
  categoryId: s.category_id ?? cached?.categoryId,
  createdAt: s.created_at ?? cached?.createdAt ?? new Date().toISOString(),
  label: cached?.label ?? arrivalLabel(s.variant_id) ?? s.variant_id
});

/** 向後端取得這個信箱的到貨通知（App 內由 App 代為呼叫；瀏覽器開發時直接呼叫）；失敗回傳 null */
const fetchSubscriptions = async (): Promise<SubscriptionDto[] | null> => {
  if (inApp()) {
    const reply = await askApp<SubscriptionDto[]>('assistive_subscriptions');
    return Array.isArray(reply) ? reply : null;
  }
  try {
    return await withMailbox((box) =>
      requestJson<SubscriptionDto[]>(
        'GET',
        `/subscriptions?mailbox_id=${encodeURIComponent(box.id)}`,
        undefined,
        { Authorization: `Bearer ${box.key}` }
      )
    );
  } catch {
    return null;
  }
};

/** 到貨通知清單：先用這台裝置記得的，後端有回應就換成後端的（含到貨狀態） */
export const loadArrivals = async (): Promise<ArrivalNotice[]> => {
  const cached = listArrivals();
  if (!hasBackend) return cached;
  const remote = await fetchSubscriptions();
  if (!remote) return cached;
  const byVariant = new Map(cached.map((a) => [a.variantId, a]));
  const merged = remote.map((s) => toNotice(s, byVariant.get(s.variant_id)));
  write(ARRIVALS_KEY, merged);
  return merged;
};

const failureCode = (e: unknown) => (e instanceof ApiError ? e.code ?? 'ERROR' : 'NETWORK');

/** 登記到貨通知。這個品項已經在等待中就直接回傳原本的登記；失敗丟出 ArrivalError。 */
export const subscribeArrival = async (
  variantId: string,
  label: string
): Promise<ArrivalNotice> => {
  const existing = listArrivals().find((a) => a.variantId === variantId && a.status !== 'arrived');
  if (existing) return existing;

  let notice: ArrivalNotice = {
    variantId,
    label,
    id: `N${Date.now().toString(36).toUpperCase()}`,
    createdAt: new Date().toISOString(),
    status: 'waiting'
  };
  if (hasBackend) {
    if (inApp()) {
      const reply = await askApp<true | { ok: false; code?: string }>('assistive_subscribe', {
        variant_id: variantId,
        on: true
      });
      if (reply !== true) {
        throw new ArrivalError(
          reply && typeof reply === 'object' ? reply.code ?? 'ERROR' : 'NETWORK'
        );
      }
    } else {
      try {
        await withMailbox((box) =>
          requestJson(
            'POST',
            '/subscriptions',
            { mailbox_id: box.id, variant_id: variantId },
            { Authorization: `Bearer ${box.key}` }
          )
        );
      } catch (e) {
        throw new ArrivalError(failureCode(e));
      }
    }
    // 取回後端的登記編號與分類
    const mine = (await fetchSubscriptions())?.find(
      (s) => s.variant_id === variantId && s.status === 'waiting'
    );
    notice = mine ? toNotice(mine, notice) : { ...notice, id: '—' };
  } else {
    await delay(600);
  }
  write(ARRIVALS_KEY, [notice, ...listArrivals().filter((a) => a.variantId !== variantId)]);
  return notice;
};

/** 取消到貨通知；失敗丟出 ArrivalError，不會顯示成已取消。 */
export const unsubscribeArrival = async (variantId: string): Promise<void> => {
  const notice = listArrivals().find((a) => a.variantId === variantId);
  if (!notice) return;
  if (hasBackend) {
    if (inApp()) {
      const reply = await askApp<true | { ok: false; code?: string }>('assistive_subscribe', {
        variant_id: variantId,
        on: false
      });
      if (reply !== true) {
        throw new ArrivalError(
          reply && typeof reply === 'object' ? reply.code ?? 'ERROR' : 'NETWORK'
        );
      }
    } else {
      try {
        await withMailbox((box) =>
          requestJson('DELETE', `/subscriptions/${encodeURIComponent(notice.id)}`, undefined, {
            Authorization: `Bearer ${box.key}`
          })
        );
      } catch (e) {
        throw new ArrivalError(failureCode(e));
      }
    }
  } else {
    await delay(400);
  }
  write(
    ARRIVALS_KEY,
    listArrivals().filter((a) => a.variantId !== variantId)
  );
};

export const deadlineText = (r: Reservation) =>
  r.pickupDeadline ? formatDate(new Date(r.pickupDeadline)) : '';

/** 期限內可以去取貨的日子，例如「11/7（週六）」 */
export const pickupDatesText = (r: Reservation) =>
  (r.pickupDates ?? []).map((d) => formatDate(new Date(d))).join(lang.value === 'en' ? ', ' : '、');

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
      return t('reservations.status.cancelled');
    case 'expired':
      return t('reservations.status.expired');
    case 'completed':
      return t('reservations.status.completed');
    case 'confirmed':
      return t('reservations.status.confirmed');
    case 'booked':
      return t('reservations.status.booked');
    default:
      return t('reservations.status.submitted');
  }
};

/**
 * 以下三個函式是給後端資料準備的轉接層（後端目前只有行事曆有對應的 API）：有資料就回傳，沒有（沒設定後端、連不上、尚未提供）就回傳 null，
 * 呼叫端要自己退回目前的行為。
 */

/** 中心逐日行事曆。GET /centers/{id}/calendar?from=YYYY-MM-DD&days=N → { days: [{ date, open, reason? }] } */
export const fetchCenterCalendar = async (
  centerId: string,
  from: string,
  days: number
): Promise<CalendarDay[] | null> => {
  if (import.meta.env.DEV && useSample())
    return (await import('./sample')).sampleCalendar(centerId, taipeiNow());
  const data = await getJson<{ days?: CalendarDay[] } | CalendarDay[]>(
    `/centers/${encodeURIComponent(centerId)}/calendar?from=${from}&days=${days}`
  );
  const list = Array.isArray(data) ? data : data?.days;
  return list?.length ? list : null;
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
