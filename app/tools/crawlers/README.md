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
