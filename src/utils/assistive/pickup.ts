/**
 * 借用取貨的日子：預約當天到取貨期限之間，中心哪幾天開、哪幾天休館，以及還剩幾個開館日可以去。
 * 資料來自預約當下後端（或畫面上算出）的 pickupDates／pickupDeadline，這裡只做整理與判斷。
 */
import { effectiveStatus } from './api';
import { centerById } from './centers';
import { taipeiNow } from './time';
import type { Reservation } from './types';

export interface PickupDay {
  date: Date;
  /** 中心那天有開館，可以去取貨 */
  open: boolean;
  isDeadline: boolean;
  isToday: boolean;
  /** 今天本來是開館日，但現在已經過了閉館時間（畫面寫「已過閉館時間」，不是「休館」） */
  pastClosing: boolean;
}

const startOfDay = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate());
const key = (d: Date) => `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`;

/** 預約當天到取貨期限的每一天（最多 7 天，期限只有 2 天，這只是防止壞資料把版面撐爆） */
export const pickupDays = (r: Reservation, now = taipeiNow()): PickupDay[] => {
  if (!r.pickupDeadline || !r.pickupDates) return [];
  const deadline = startOfDay(new Date(r.pickupDeadline));
  const start = startOfDay(new Date(r.createdAt));
  const open = new Set(r.pickupDates.map((d) => key(new Date(d))));
  const today = key(now);
  const days: PickupDay[] = [];
  for (
    let day = start;
    day <= deadline && days.length < 7;
    day = new Date(day.getFullYear(), day.getMonth(), day.getDate() + 1)
  ) {
    const isToday = key(day) === today;
    const isOpen = open.has(key(day));
    const center = centerById(r.centerId);
    days.push({
      date: day,
      open: isOpen,
      isDeadline: key(day) === key(deadline),
      isToday,
      pastClosing:
        isToday &&
        !isOpen &&
        !!center?.openDays.includes(day.getDay()) &&
        now.getHours() * 60 + now.getMinutes() >= closingMinutes(r)
    });
  }
  return days;
};

export interface PickupRemaining {
  /** 現在起還能去取貨的開館日數（今天已經過了閉館時間的不算） */
  count: number;
  /** 最後一個還能去的日子 */
  last?: Date;
  lastIsToday: boolean;
}

const closingMinutes = (r: Reservation) => {
  const hours = centerById(r.centerId)?.hours ?? [];
  const to = hours[hours.length - 1]?.to;
  if (!to) return 24 * 60;
  const [h, m] = to.split(':').map(Number);
  return h * 60 + m;
};

/** 借用預約還剩幾個開館日可以去取貨；不是「已預約，待取貨」或沒有開館日資料時回傳 null */
export const pickupRemaining = (r: Reservation, now = taipeiNow()): PickupRemaining | null => {
  if (effectiveStatus(r, now) !== 'booked' || !r.pickupDates) return null;
  const today = startOfDay(now);
  const minutes = now.getHours() * 60 + now.getMinutes();
  const left = r.pickupDates
    .map((d) => startOfDay(new Date(d)))
    .filter((d) => d > today || (key(d) === key(today) && minutes < closingMinutes(r)))
    .sort((a, b) => a.getTime() - b.getTime());
  const last = left[left.length - 1];
  return {
    count: left.length,
    last,
    lastIsToday: !!last && key(last) === key(today)
  };
};
