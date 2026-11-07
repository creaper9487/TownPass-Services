// 抓臺北市輔具資源整合資訊網「輔具衛教」的全部文章，寫成 src/data/assistive-education.json。
// 執行：pnpm assistive:crawl-education（需要連網；官網更新文章後重跑一次即可）
// 官網是伺服器直接產生的 HTML：列表分頁（每頁 5 篇），每篇一頁，內文用 <br> 分行，影片是 YouTube iframe。
// 內文逐行原樣保存（不改字），畫面上的分段、步驟、小標在 src/utils/assistive/education.ts 解析。
import { writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

const BASE = 'https://tpap.gov.taipei';
const OUT = fileURLToPath(new URL('../../src/data/assistive-education.json', import.meta.url));

const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const get = async (path) => {
  for (let i = 0; i < 4; i++) {
    try {
      const res = await fetch(BASE + path, { headers: { 'accept-language': 'zh-TW' } });
      if (res.ok) return await res.text();
    } catch {
      /* 官網偶爾拒絕連線：等一下再試 */
    }
    await wait(2500);
  }
  throw new Error(`抓不到 ${path}`);
};

const named = {
  nbsp: ' ', amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", hellip: '…', mdash: '—', ndash: '–',
  ldquo: '“', rdquo: '”', lsquo: '‘', rsquo: '’', bull: '•', middot: '·'
};
const decode = (s) =>
  s.replace(/&(?:#(\d+)|#x([\da-f]+)|([a-z]+));/gi, (m, dec, hex, name) =>
    dec ? String.fromCodePoint(Number(dec)) : hex ? String.fromCodePoint(parseInt(hex, 16)) : (named[name.toLowerCase()] ?? m)
  );
// ⠀（U+2800，點字空白）是文章裡拿來當空行的字元，不是內容
const text = (html) => decode(html.replace(/<[^>]+>/g, ' ')).replace(/[\s\u2800]+/g, ' ').trim();

const roc = (d) => {
  const m = d.match(/民國(\d+)年(\d+)月(\d+)日/);
  return m ? `${Number(m[1]) + 1911}-${m[2].padStart(2, '0')}-${m[3].padStart(2, '0')}` : '';
};

const items = [];
for (let offset = 0; ; offset += 5) {
  const path =
    offset === 0
      ? '/app37/healthEducationView/index?lang=zh_TW'
      : `/app37/healthEducationView/query?offset=${offset}&max=5&format=&lang=zh_TW`;
  const html = await get(path);
  const found = [
    ...html.matchAll(
      /<div class="card-title">(.*?)<\/div>.*?<li>&nbsp;(.*?)<\/li>.*?healthEducationView\/detail\?healthid=(\d+)/gs
    )
  ];
  if (!found.length) break;
  for (const [, title, date, id] of found) items.push({ id, title: text(title), date: text(date) });
  await wait(800);
}

for (const item of items) {
  const html = await get(`/app37/healthEducationView/detail?healthid=${item.id}&lang=zh_TW`);
  // 標題與日期也在同名的 div 裡；內文是「封面圖區塊」之後的那一個
  const body =
    html.match(/<div class="blog-img">[\s\S]*?<div class="blog margin-bottom-40">([\s\S]*?)<\/div>/)?.[1] ?? '';
  const video = html.match(/<iframe[^>]+src="https?:\/\/www\.youtube\.com\/embed\/([\w-]+)/)?.[1];
  const cover = html.match(/<div class="blog-img">\s*<img[^>]+src="([^"]+)"/)?.[1];
  // 有些文章用 <br> 分行，有些用 <p>／<ul><li>：統一成「一行一個字串，空字串 = 段落分隔，• 開頭 = 清單項目」
  const lines = body
    .replace(/<li[^>]*>/gi, '\n• ')
    .replace(/<\/(?:p|ul|ol|h[1-6]|div)>/gi, '\n\n')
    .replace(/<br\s*\/?>/gi, '\n')
    .split('\n')
    .map((l) => text(l))
    // 「連結網址：https://youtu.be/…」只是重複放這支影片的網址，頁面上已經直接播放，不再重複。
    .filter((l) => !/^連結網址：\s*https?:\/\/youtu\.be\//.test(l))
    .filter((l, i, all) => l || (i > 0 && all[i - 1]));
  while (lines.length && !lines[0]) lines.shift();
  while (lines.length && !lines[lines.length - 1]) lines.pop();

  const prefix = item.title.match(/^【(.+?)】/);
  items[items.indexOf(item)] = {
    id: item.id,
    title: item.title,
    category: prefix?.[1] ?? '',
    name: item.title.replace(/^【.+?】\s*/, ''),
    date: item.date,
    iso: roc(item.date),
    lines,
    ...(video ? { video } : {}),
    ...(cover ? { cover } : {}),
    source: `${BASE}/app37/healthEducationView/detail?healthid=${item.id}`
  };
  await wait(800);
}

items.sort((a, b) => b.iso.localeCompare(a.iso) || Number(b.id) - Number(a.id));
await writeFile(OUT, JSON.stringify(items, null, 2) + '\n');
console.log(`寫入 ${items.length} 篇 → ${OUT}`);
console.log(`有影片 ${items.filter((i) => i.video).length} 篇、有封面圖 ${items.filter((i) => i.cover).length} 篇`);
