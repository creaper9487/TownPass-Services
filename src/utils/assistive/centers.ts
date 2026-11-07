import type { CalendarDay, Center } from './types';
import { taipeiNow } from './time';
import { lang, tx } from '@/i18n/assistive';

/**
 * 臺北市三家輔具中心。資料來源：臺北市輔具資源整合資訊網（tpap.gov.taipei）。
 * 座標為約略值，只拿來排序「離我最近」，導航請用地址。
 */
export const centers: Center[] = [
  {
    id: 'heyi',
    name: '臺北市合宜輔具中心',
    shortName: '合宜',
    districts: ['中山區', '大同區', '士林區', '北投區'],
    address: '臺北市中山區玉門街 1 號',
    phone: '02-7713-7760',
    openDays: [2, 3, 4, 5, 6],
    hours: [
      { from: '09:00', to: '12:00' },
      { from: '13:30', to: '17:00' }
    ],
    lat: 25.0705,
    lng: 121.5183
  },
  {
    id: 'south',
    name: '臺北市南區輔具中心',
    shortName: '南區',
    districts: ['內湖區', '信義區', '文山區', '南港區'],
    address: '臺北市信義區大道路 116 號 3 樓之 2',
    addressNote: '廣慈衛福大樓，從西 2 門 B 電梯廳進入',
    phone: '02-2720-7364',
    openDays: [1, 2, 3, 4, 5],
    hours: [
      { from: '09:00', to: '12:00' },
      { from: '13:30', to: '17:00' }
    ],
    lat: 25.0345,
    lng: 121.5815
  },
  {
    id: 'west',
    name: '臺北市西區輔具中心',
    shortName: '西區',
    districts: ['中正區', '萬華區', '大安區', '松山區'],
    address: '臺北市中山區長安西路 5 巷 2 號 1、2 樓',
    addressNote: '臺北市政府衛生局舊址後方',
    phone: '02-2523-7902',
    openDays: [2, 3, 4, 5, 6],
    hours: [
      { from: '09:00', to: '12:00' },
      { from: '13:30', to: '17:00' }
    ],
    lat: 25.0487,
    lng: 121.5137
  }
];

export const taipeiDistricts = centers.flatMap((c) => c.districts);

const weekdayLabel = ['日', '一', '二', '三', '四', '五', '六'];
const weekdayEn = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

/** 畫面上顯示的中心名稱（跟著語言） */
export const centerName = (c: Center) => tx(c.name);
export const centerShort = (c: Center) => tx(c.shortName);

export const centerById = (id: string) => centers.find((c) => c.id === id);

export const centerByDistrict = (district: string) =>
  centers.find((c) => c.districts.includes(district));

/** 「週二至週六」這類開館日描述（英文：Tue–Sat） */
export const openDaysText = (c: Center) => {
  const days = [...c.openDays].sort();
  const contiguous = days.every((d, i) => i === 0 || d === days[i - 1] + 1);
  if (lang.value === 'en') {
    return contiguous && days.length > 1
      ? `${weekdayEn[days[0]]}–${weekdayEn[days[days.length - 1]]}`
      : days.map((d) => weekdayEn[d]).join(', ');
  }
  return contiguous && days.length > 1
    ? `週${weekdayLabel[days[0]]}至週${weekdayLabel[days[days.length - 1]]}`
    : days.map((d) => `週${weekdayLabel[d]}`).join('、');
};

export const hoursText = (c: Center) =>
  c.hours.map((h) => `${h.from}–${h.to}`).join(lang.value === 'en' ? ', ' : '、');

const toMinutes = (hhmm: string) => {
  const [h, m] = hhmm.split(':').map(Number);
  return h * 60 + m;
};

export const isOpenAt = (c: Center, date: Date) => {
  if (!c.openDays.includes(date.getDay())) return false;
  const now = date.getHours() * 60 + date.getMinutes();
  return c.hours.some((h) => now >= toMinutes(h.from) && now < toMinutes(h.to));
};

const startOfDay = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate());
const addDays = (d: Date, n: number) => {
  const r = startOfDay(d);
  r.setDate(r.getDate() + n);
  return r;
};

export interface PickupWindow {
  /** 取貨期限（預約日起 2 天內，含當日） */
  deadline: Date;
  /** 期限內該中心還有哪幾天開館（今天若已過營業時間則不算） */
  openDates: Date[];
  /** 期限內因行事曆而休館的日子與原因（國定假日、臨時休館）；沒有行事曆資料時為空 */
  closures: { date: Date; reason?: string }[];
}

export const dateKey = (d: Date) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;

const calendarMap = (days?: CalendarDay[] | null) =>
  new Map((days ?? []).map((d) => [d.date, d] as const));

/**
 * 二手輔具「預約後 2 天內（含當日）於開館時間取貨，逾期自動取消」。
 * 這裡算出期限內真正還能去的日子，避免預約了卻剛好遇到休館日。
 *
 * 有行事曆（逐日開館資料）就以行事曆為準，沒有就用星期規則。
 * 休館時取件期限會不會順延，中心尚未確認，所以這裡不順延，只標示「期限內沒有開館日」。
 */
export const pickupWindow = (
  c: Center,
  now = taipeiNow(),
  calendar?: CalendarDay[] | null
): PickupWindow => {
  const byDate = calendarMap(calendar);
  const isOpenOn = (d: Date) => {
    const entry = byDate.get(dateKey(d));
    return entry ? entry.open : c.openDays.includes(d.getDay());
  };
  const today = startOfDay(now);
  const lastHour = c.hours[c.hours.length - 1].to;
  const todayStillPossible =
    isOpenOn(today) && now.getHours() * 60 + now.getMinutes() < toMinutes(lastHour);
  const days = [0, 1].map((n) => addDays(today, n));
  const openDates = days.filter((d, i) => (i === 0 ? todayStillPossible : isOpenOn(d)));
  const closures = days
    .map((d) => ({ date: d, entry: byDate.get(dateKey(d)) }))
    .filter((x) => x.entry && !x.entry.open)
    .map((x) => ({ date: x.date, reason: x.entry?.reason }));
  return { deadline: addDays(today, 1), openDates, closures };
};

/**
 * 近期的「例外休館」：行事曆說休館、但依一般星期規則本來該開的日子（國定假日、臨時休館）。
 * 一般的週末休館不算公告。
 */
export const upcomingClosures = (
  c: Center,
  calendar: CalendarDay[] | null | undefined,
  now = taipeiNow(),
  horizonDays = 14
) => {
  const today = startOfDay(now);
  const end = addDays(today, horizonDays);
  return (calendar ?? [])
    .map((d) => ({ day: d, date: new Date(`${d.date}T00:00:00`) }))
    .filter(
      ({ day, date }) =>
        !day.open && date >= today && date <= end && c.openDays.includes(date.getDay())
    )
    .map(({ day, date }) => ({ center: c, date, reason: day.reason }));
};

export const formatDate = (d: Date) =>
  lang.value === 'en'
    ? `${weekdayEn[d.getDay()]} ${d.getMonth() + 1}/${d.getDate()}`
    : `${d.getMonth() + 1}/${d.getDate()}（週${weekdayLabel[d.getDay()]}）`;

/** 任兩點間的粗略距離（公里） */
export const kmBetween = (lat1: number, lng1: number, lat2: number, lng2: number) =>
  Math.hypot((lat1 - lat2) * 111, (lng1 - lng2) * 101);

/** 兩點間的粗略距離（公里） */
export const distanceKm = (c: Center, lat: number, lng: number) =>
  Math.hypot((c.lat - lat) * 111, (c.lng - lng) * 101);

export const nearestCenter = (lat: number, lng: number) =>
  [...centers].sort((a, b) => distanceKm(a, lat, lng) - distanceKm(b, lat, lng))[0];

export const mapUrl = (c: Center) =>
  `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(c.address.replace(/\s/g, ''))}`;

/** 官方網站「借用須知」裡的中心資料表（原文） */
export const officialCenterRows: { name: string; hours: string; address: string; phone: string }[] =
  [
    {
      name: '臺北市合宜輔具中心',
      hours: '周二至周六 9:00-12:00, 13:30-17:00',
      address: '臺北市中山區玉門街1號',
      phone: '02-77137760'
    },
    {
      name: '臺北市南區輔具中心',
      hours: '周一至周五 9:00-12:00, 13:30-17:00',
      address: '臺北市信義區大道路116號3F-2(廣慈衛福大樓 -從西2門B電梯廳進入)',
      phone: '02-27207364'
    },
    {
      name: '臺北市西區輔具中心',
      hours: '周二至周六 9:00-12:00, 13:30-17:00',
      address: '臺北市中山區長安西路5巷2號1、2樓(臺北市政府衛生局舊址後方)',
      phone: '02-2523-7902'
    }
  ];
