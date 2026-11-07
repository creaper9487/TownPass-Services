/** 開發用範例資料（只在 DEV 且啟用 assistive.sample 時載入，不會進入正式版） */
import type { CalendarDay, CenterStockMap, RentalStore, VariantFit } from './types';

const pad = (n: number) => String(n).padStart(2, '0');
const key = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

export const sampleRentalStores = (categoryId: string): RentalStore[] =>
  [
    {
      id: 's1',
      name: '範例醫材行（中山店）',
      address: '臺北市中山區南京東路二段 1 號',
      phone: '02-2511-0001',
      categories: ['1', '7', '9'],
      lat: 25.0522,
      lng: 121.5336
    },
    {
      id: 's2',
      name: '範例輔具生活館（信義店）',
      address: '臺北市信義區松仁路 100 號',
      phone: '02-2720-0002',
      categories: ['1', '2', '3'],
      lat: 25.0355,
      lng: 121.5683
    },
    {
      id: 's3',
      name: '範例居家照護（大安店）',
      address: '臺北市大安區復興南路二段 50 號',
      phone: '02-2700-0003',
      categories: ['1', '6'],
      lat: 25.0278,
      lng: 121.5436
    },
    {
      id: 's4',
      name: '範例復健器材（內湖店）',
      address: '臺北市內湖區成功路四段 10 號',
      phone: '02-2790-0004',
      categories: ['4'],
      lat: 25.0841,
      lng: 121.5915
    }
  ].filter((s) => s.categories.includes(categoryId));

/** 範例行事曆：明天休館（國定假日），後天正常 */
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
