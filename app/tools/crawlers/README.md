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
| 1 | 🔴 合併前必改 | `_calendar_source.py` | 最新消息裡只要有一則提到「休館」卻讀不出中心或日期（例如圖片公告），或最新消息頁改版、連不上，`_fetch_closures()` 就 raise → 行事曆失敗 → **借用預約也失敗**。實測行事曆 API、`POST /reservations`（borrow）都回 500。 | 休館公告抓取或解析失敗時：記 log（不含個資）、改用上一次成功的結果；沒有上一次就用 `_reviewed_closures()`。讀不懂的單則公告略過並記 log，不要讓整份失敗。補一個測試：`_fetch_closures` 拋錯時 `fetch_center_calendar` 仍回傳正確天數。 | ☑ 已修正並補回歸測試 |
| 2 | 🟠 12/18 前要改 | `_calendar_source.py` | `GOVERNMENT_CALENDARS` 只有 2026 年，查到 2027 年就 `NotImplementedError`：2026-12-19 起前端預設查 14 天會回 501；2026-12-31 借用預約會失敗。 | 補 2027 年（民國 116 年）的官方 CSV 網址（data.gov.tw/dataset/14718）。若 codefest 在 12/18 前結束可先不做。 | ☑ 已加入官方 2027 年 CSV |
| 3 | 🟡 要跟後端確認 | `stock.py`、`_borrow_source.py` | 後端每 45 秒同步庫存，每次約 13 個請求（1 個分類頁 + 每個分類 1 頁，間隔 1 秒），約每小時 1000 個請求打市府網站。 | 後端會把 `stock_sync_seconds` 調慢（2～5 分鐘）；正式上線前跟中心確認頻率。爬蟲這邊不用改。 | ☐ 後端處理 |
| 4 | ⚪ 建議 | `preview.py`、`PREVIEW.md`、`preview_test.py` | 這些是開發時預覽資料用的工具，不是正式執行要用的，放在 `app/tools/crawlers/` 會混在正式程式裡。 | 搬到專案根目錄的 `scripts/`（`preview_test.py` 一起搬或改到 `tests/`）。不擋合併。 | ☑ 工具與說明已搬到 scripts，測試搬到 tests |

改完把「狀態」打勾，push 到 `crawler`，然後開 PR `crawler` → `developer`。

### Review 修正與驗證（2026-11-07）

- 第 1 項：單則公告 HTTP／解析失敗會記錄 warning 並略過，保留已知休館日期；整批失敗沿用最近成功結果，首次失敗採已核對公告。回退結果暫存五分鐘再試。日誌只含錯誤類別，不含例外本文、公告內容或個資。
- 第 2 項：2027 年來源取自 [官方資料集 14718](https://data.gov.tw/dataset/14718)，已實際下載並驗證 365 天資料；補上 12/19 的 14 天跨年查詢及 12/31 的兩天取貨區間測試。
- 第 4 項：執行 `python -m scripts.preview`；測試位於 `tests/test_preview.py`，使用方式見 `scripts/PREVIEW.md`。
- `python -m pytest -q`：36 個測試通過，包含公告失敗時行事曆 API 回 200、借用預約回 201；全部離線執行。
- `python -m app.tools.crawlers.check all`：實際連官網，catalog／stock／centers／calendar 全部通過（12 類、62 款）。
- router、schemas、check、runner、爬蟲匯出介面與庫存排程頻率均未修改；第 3 項仍由後端調整。

### 2026-11-07 13:33 — 複查 commit `34fbf68` Fix closure announcement fallback and support 2027 calendar

審查結果：測試 36 個全過。上次的第 1、2、4 項都確認修好，第 3 項仍由後端處理。
這次又找到 2 個問題，**修完第 5 項就可以開 PR 合回 `developer`**。

確認修好：
- 第 1 項：單則公告失敗會略過並記 warning（只記錯誤類別，不記內容），整批失敗時沿用上次成功的結果，第一次就失敗則用人工核對過的日期；回退結果暫存 5 分鐘。有測試證明公告失敗時行事曆回 200、借用回 201。
- 第 2 項：已加入 2027 年官方 CSV，並有 12/19 查 14 天、12/31 借用的跨年測試。
- 第 4 項：預覽工具搬到 `scripts/`，測試搬到 `tests/test_preview.py`。

要改的東西：

| # | 嚴重度 | 檔案 | 問題 | 怎麼改 | 狀態 |
|---|---|---|---|---|---|
| 5 | 🔴 合併前必改 | `_calendar_source.py` | 跟第 1 項同一類問題，換成政府假日 CSV：`_load_holidays()` 在**執行時**才去 dgpa.gov.tw 下載 CSV，下載失敗（網站掛掉、改網址、逾時）就 raise → 行事曆 500 → 借用預約也失敗。實測讓下載拋 `ConnectError`，行事曆 API 回 500。而且 `lru_cache` 不會快取例外，所以網站掛掉期間每個借用請求都會重試、等 20 秒逾時。 | 把 2026、2027 年的 CSV 檔直接放進 repo（例如 `app/tools/crawlers/data/holidays_2026.csv`），`_load_holidays()` 改成讀本機檔，不要在執行時下載。一年只更新一次，手動更新就好；原本的網址留在註解裡記錄來源。補測試：沒有網路時行事曆仍回 200。 | ☑ 已內建兩年 CSV，補斷網回歸測試 |
| 6 | ⚪ 建議 | `_calendar_source.py` `_fetch_closures()` | 為了保留「讀不懂的那則公告」，現在每次都把上一次的全部結果合併進來（`result.update(_closures)`），所以中心**撤回或更正**某個休館日之後，那天會一直被當成休館，直到程式重啟。 | 只保留「這次讀取失敗的那幾則公告」上次解析出來的日期，其他照這次的結果。或者至少在 README 註明「撤回休館需重啟後端」。不擋合併。 | ☑ 改為每則 newsid 快取，下架／更正會移除舊日期 |

### 第 5、6 項修正與驗證（2026-11-07）

- 政府日曆改讀 `data/holidays_2026.csv`、`data/holidays_2027.csv`，兩份各 365 天，保留官方欄位與來源。執行期不再下載政府 CSV；年度手動更新方式見 `data/README.md`，部署需包含這個資料夾。
- 補斷網測試：封鎖所有對外 HTTP，行事曆跨年查詢仍回 200、12/31 借用仍回 201，取貨開館日正確排除 2027/1/1；無 dgpa.gov.tw 請求。
- 公告按 `newsid` 分別保存解析結果。這次成功讀取的公告直接替換日期，只有讀取失敗的單則保留自己的舊結果；完整清單中的下架公告會清除，明確「取消／撤銷／撤回休館」可清空該則日期。整批失敗的回退機制維持不變。
- 補公告更正、下架、明確取消及單則讀不懂的測試；既有已人工核對的歷史公告仍保留於 `_reviewed_closures()`。
- `python -m pytest -q`：40 個測試通過；`python -m app.tools.crawlers.check all`：連官網四項皆通過，12 類、62 款。
- router、schemas、check、runner、匯出介面與庫存排程頻率均未修改；第 3 項仍由後端處理。

### 2026-11-07 13:51 — 複查 commit `affb634` Bundle offline holiday calendars and refresh notices independently

審查結果：✅ **通過，可以開 PR `crawler` → `developer`。** 測試 40 個全過。

確認修好：
- 第 5 項：政府假日改讀 `data/holidays_2026.csv`、`data/holidays_2027.csv`，執行時不再連 dgpa.gov.tw。
  審查環境連不到任何外部網站，`GET /centers/heyi/calendar?from=2026-12-28&days=7` 仍回 200，
  跨年資料正確：12/28（一）合宜例假休館、12/29～12/31 開館、2027/1/1 開國紀念日休館、1/2（六）開館。
  抽查 2026 年 10 月以後的假日（10/9 補假、10/10 國慶日、10/25、10/26 補假、12/25 行憲紀念日）與 2027 年春節都正確。
- 第 6 項：休館公告改成依 `newsid` 各自保存，讀取成功的公告直接替換舊日期，只有讀取失敗的那則保留舊結果；
  公告下架或明確寫「取消／撤銷／撤回休館」會清掉日期。比原本建議的做法更完整。
- `data/README.md` 寫清楚來源、授權、每年更新步驟，很好。

剩下：
- 第 3 項（庫存同步頻率）由後端在 `developer` 調整，不影響這次合併。
- 每年要記得放新一年的假日 CSV（照 `data/README.md` 的步驟）；2028 年的檔案要在 2027 年 12 月中前放進來。
