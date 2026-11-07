# 輔具借用／評估資料

本次已接入四個正式資料函式：fetch_catalog、fetch_stock、fetch_centers、fetch_center_calendar。
目錄與庫存使用相同的官方款式 ID。程式只讀取公開頁面，沒有送出預約、候補或取消。

## 範圍

- 輔具借用：目錄、照片網址、規格、庫存、候補人數與借用規則。
- 借用及評估中心：地址、電話、服務行政區、分段開館時間與經緯度。
- 開館行事曆：中心固定開館日、官方假日、可辨識的文字休館公告。
- 評估目前只取得服務入口；申請欄位、時段及實際送件尚待確認。
- 官方預約查詢／取消尚未串接。
- 不再抓取人口、里界、捷運電梯、商業租賃門市、補助統計或回收資料。舊試跑資料保留供回溯。

## 執行

在後端專案根目錄：

```powershell
.\.venv\Scripts\python.exe -X utf8 -m app.tools.crawlers.check all
.\.venv\Scripts\python.exe -X utf8 -m pytest -q
.\.venv\Scripts\python.exe -X utf8 -m scripts.preview
```

只檢查四種資料可加 --core-only。重新整理既有 HTML 解析結果可加 --reuse-cache，
但這會使用舊的借用快照；中心與行事曆仍走正式函式。正式函式不讀預覽快取檔。

結果在 .cache/assistive-preview/時間/，結束時會印出完整路徑；已由原有 .gitignore 排除。

| 檔案 | 用途 |
|---|---|
| summary.md / summary.json | 筆數、格式檢查、限制 |
| source_manifest.json | 預覽 HTTP 來源、抓取時間、快取狀態；不含正式行事曆內部請求 |
| catalog.json / .csv | 分類與款式，JSON 對齊 id/image/specs/attrs |
| stock.json / .csv | 款式代碼、剩餘數量與候補人數 |
| availability_preview.csv | 名稱、規格與庫存合併表，可用 Excel 開啟 |
| stock_observations.json | 原始數值與空白轉 0 的依據 |
| centers.json / centers_preview.json | 三間中心，包含已驗證的建物座標 |
| calendar_preview.json | 各中心預設連續 14 天的開館日及分段時間 |
| pages/ | 借用規則、評估服務入口；不是已完成的送件表單 |

## 實作限制

- 實測分類在 rentView/additem；每款庫存及候補在 vehicleDetail/{分類ID}。一次完整更新需 1 個分類頁加每分類 1 個 HTML，沒有下載照片或進入單品操作頁。這與 README 的「不進詳細頁」假設不同，需和後端確認正式高頻使用方式。
- 目錄和庫存在同一 process 共用最長 30 秒的完整快照，避免短時間重複請求。網路、結構或數值解析失敗會拋出例外，不把失敗當成空庫存。
- 官網省略候補欄但顯示可預約按鈕時，依 README 將候補轉為 0；缺少必要欄位或出現未知文字則失敗。座寬「15或16吋」保留原文，不硬選一個數值。
- 中心資料於 2026-11-07 核對官網；座標核對官方頁內 Google Maps 的地點名稱、地址及電話。座標是建物位置，不代表無障礙入口或樓層。執行時不使用付費地圖 API。
- 日曆使用 repo 內的 2026～2027 年官方 CSV，可離線查詢跨年區間；執行期不下載政府日曆。年度更新與來源見 `app/tools/crawlers/data/README.md`。
- 政府例行週六休假不會使合宜、西區自動休館。補班日只有中心明確公告開館才應覆寫；目前採每週時段，不推測額外開館。
- 休館公告每 5 分鐘嘗試更新；單則失敗只保留同一 newsid 上次解析的日期。完整清單讀取成功後，已下架公告會移除，更正日期與明確取消休館公告會取代舊結果。整批失敗才沿用完整上次結果；首次失敗用已核對公告，五分鐘後再試。日誌不含個資。影像型公告及未公開的臨時異動仍需中心確認。
- 前端自行保存的預約查詢／取消由既有後端流程負責，這不代表已同步官方中心系統。center_forward.py 仍保留未實作。

額外的 HTML 解析測試：

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pytest tests/test_preview.py -q
```
