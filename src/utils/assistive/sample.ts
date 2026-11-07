/** 開發用範例資料（只在 DEV 且啟用 assistive.sample 時載入，不會進入正式版） */
import type { CalendarDay, CenterStockMap, VariantFit } from './types';

const pad = (n: number) => String(n).padStart(2, '0');
const key = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

export const sampleCalendar = (centerId: string, today: Date): CalendarDay[] => {
  const day = (n: number) => new Date(today.getFullYear(), today.getMonth(), today.getDate() + n);
  const days: CalendarDay[] = [];
  for (let n = 0; n < 14; n += 1) {
    const d = day(n);
    days.push({ date: key(d), open: !(n === 1 && centerId !== 'south') });
  }
  days[1].reason = centerId !== 'south' ? '國定假日' : undefined;
  days[5].open = false;
  days[5].reason = '臨時休館（設備維護）';
  return days;
};

export const sampleCenterStock = (): CenterStockMap => ({
  heyi: { stock: 3 },
  south: { stock: 0 },
  west: { stock: 1 }
});

export const sampleVariantFit: Record<string, VariantFit> = {};
