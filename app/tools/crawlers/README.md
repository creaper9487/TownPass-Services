# 爬蟲組說明

## 要寫哪裡

只改這個資料夾（`app/tools/crawlers/`）裡的 4 個檔案，把每個 function 裡的
`raise NotImplementedError(...)` 換成你的程式。每個 function 的註解都寫了：網址、步驟、
「網頁上看到的 → 要填的欄位」對照表、注意事項、回傳範例，最下面還有可以照著改的範本程式。

| 檔案 | function | 要爬什麼 | 誰寫 |
|---|---|---|---|
| `catalog.py` | `fetch_catalog()` | 可以借哪些輔具：12 類、62 款的名稱、照片、規格 | 爬蟲組 |
| `stock.py` | `fetch_stock()` | 每款還剩幾台、幾人在排隊（每 45 秒跑一次） | 爬蟲組 |
| `centers.py` | `fetch_centers()` | 3 間中心的地址、電話、開館日與時段、經緯度（可寫死） | 爬蟲組 |
| `center_calendar.py` | `fetch_center_calendar()` | 接下來每天有沒有開館（國定假日、臨時休館） | 爬蟲組 |
| `center_forward.py` | `forward_reservation()` | 不是爬蟲，是把預約送到中心；等中心決定介接方式 | 先不用寫 |

**不要改**：`schemas.py`（回傳格式，看就好）、`check.py`、`runner.py`、`__init__.py`。
格式要改的話跟後端講，後端改完會同步到 `crawler` 分支。

## 規則

1. 寫一般的同步 function 就好，可以用 `requests`、`BeautifulSoup`（要用新套件就加到 `requirements.txt`）。
2. 回傳 `schemas.py` 裡的 model，或欄位一樣的 dict 都可以。
3. 還沒寫好就保持 `raise NotImplementedError`，API 會回 501，不會壞掉。
4. 代碼（`id`、`variant_id`）一律用官網自己的代碼，每次爬都要一樣；
   `fetch_stock` 的 `variant_id` 要等於 `fetch_catalog` 款式的 `id`。
5. 時間一律 `"HH:MM"`（`"08:30"`，不是 `"8:30"`）；星期一律 1=星期一 … 7=星期日。
6. 不要 print / log 任何個資。

## 寫完怎麼檢查

在專案根目錄：

```bash
python -m app.tools.crawlers.check stock     # 或 catalog / centers / calendar / all
```

會實際跑你的 function、檢查格式，錯的話會告訴你哪一筆哪個欄位錯。全部 ✓ 才 commit。

## Git

```bash
git checkout crawler
git pull origin crawler          # 後端更新 developer 時會同步到 crawler，開工前先 pull
# …寫程式、跑 check…
git add app/tools/crawlers
git commit -m "fetch_stock: 完成"
git push origin crawler
```

寫好後開 PR：`crawler` → `developer`。

## Code Review

### 2026-11-07 13:04 — commit `3039c5c` Implement assistive borrowing data crawlers

審查結果：測試 28 個全過，`check centers` 格式正確（`catalog`、`stock` 需連官網，審查環境連不到，未實測）。
整體寫得很好，**修完第 1 項才能合回 `developer`**。

做得好的地方：
- 使用官網真實代碼（`/rentView/additem`、`/vehicleDetail/{id}`），目錄與庫存代碼一致
- 抓取失敗直接拋錯，不會回空清單或假 0 蓋掉有效庫存
- 目錄與庫存共用 30 秒快照，不重複請求
- 中心資料有標註官方來源；休館公告處理民國年、日期區間、「將於…開館」不算休館
- 離線測試完整，不會真的連官網

要改的東西：

| # | 嚴重度 | 檔案 | 問題 | 怎麼改 | 狀態 |
|---|---|---|---|---|---|
| 1 | 🔴 合併前必改 | `_calendar_source.py` | 最新消息裡只要有一則提到「休館」卻讀不出中心或日期（例如圖片公告），或最新消息頁改版、連不上，`_fetch_closures()` 就 raise → 行事曆失敗 → **借用預約也失敗**。實測行事曆 API、`POST /reservations`（borrow）都回 500。 | 休館公告抓取或解析失敗時：記 log（不含個資）、改用上一次成功的結果；沒有上一次就用 `_reviewed_closures()`。讀不懂的單則公告略過並記 log，不要讓整份失敗。補一個測試：`_fetch_closures` 拋錯時 `fetch_center_calendar` 仍回傳正確天數。 | ☐ |
| 2 | 🟠 12/18 前要改 | `_calendar_source.py` | `GOVERNMENT_CALENDARS` 只有 2026 年，查到 2027 年就 `NotImplementedError`：2026-12-19 起前端預設查 14 天會回 501；2026-12-31 借用預約會失敗。 | 補 2027 年（民國 116 年）的官方 CSV 網址（data.gov.tw/dataset/14718）。若 codefest 在 12/18 前結束可先不做。 | ☐ |
| 3 | 🟡 要跟後端確認 | `stock.py`、`_borrow_source.py` | 後端每 45 秒同步庫存，每次約 13 個請求（1 個分類頁 + 每個分類 1 頁，間隔 1 秒），約每小時 1000 個請求打市府網站。 | 後端會把 `stock_sync_seconds` 調慢（2～5 分鐘）；正式上線前跟中心確認頻率。爬蟲這邊不用改。 | ☐ 後端處理 |
| 4 | ⚪ 建議 | `preview.py`、`PREVIEW.md`、`preview_test.py` | 這些是開發時預覽資料用的工具，不是正式執行要用的，放在 `app/tools/crawlers/` 會混在正式程式裡。 | 搬到專案根目錄的 `scripts/`（`preview_test.py` 一起搬或改到 `tests/`）。不擋合併。 | ☐ |

改完把「狀態」打勾，push 到 `crawler`，然後開 PR `crawler` → `developer`。
