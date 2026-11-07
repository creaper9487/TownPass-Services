# taipei-codefest-2026-Backend

臺北市輔具預約後端（FastAPI）。**前端串接說明：[docs/FRONTEND.md](docs/FRONTEND.md)**

只服務臺北市 12 個行政區。API 基準路徑 `/assistive/v1`，啟動後看 http://192.168.88.208:8000/docs（IP / port 在 `.env` 的 `HOST`、`PORT` 改）

## 分層

```
routers/   HTTP 層：參數、header、狀態碼、ETag/304。不寫邏輯。
   ↓
features/  商業邏輯：<feature>/schemas.py + repository.py（資料，目前記憶體）+ service.py
   ↓
tools/     共用工具與爬蟲：crawlers/（爬蟲組實作）、exceptions、security、push…
```

```
app/
├── main.py                 # 進入點（可直接 python app/main.py）
├── config.py
├── routers/                # catalog, centers, stock, mailboxes, reservations, subscriptions, hooks
├── features/
│   ├── catalog/  centers/  stock/  mailbox/  subscription/
│   ├── reservation/  forwarding/（送件佇列）  hooks/（中心 webhook）
│   └── jobs.py             # 背景排程：庫存同步、逾期掃描、送件
└── tools/
    ├── crawlers/           # ★ 爬蟲組寫這裡
    │   ├── schemas.py      # 回傳格式（契約）
    │   ├── catalog.py      # fetch_catalog()
    │   ├── stock.py        # fetch_stock()
    │   ├── centers.py      # fetch_centers()
    │   ├── center_calendar.py  # fetch_center_calendar()
    │   ├── center_forward.py   # forward_reservation()
    │   └── check.py        # 爬蟲格式自我檢查
    ├── exceptions.py       # problem+json 錯誤碼
    ├── security.py  districts.py（臺北市 12 區 → 中心）  push.py  cache.py  timeutil.py  http_client.py  logger.py
```

## 爬蟲（tools/crawlers）

寫「同步」function 即可，回傳符合 `schemas.py` 的格式；還沒寫好前保持 `raise NotImplementedError`（API 回 501）。

| function | 資料來源 | 回傳 | 用在 |
|---|---|---|---|
| `fetch_catalog()` | tpap.gov.taipei/app37/rentView/index | `list[CatalogCategory]` | `GET /catalog` |
| `fetch_stock()` | 同上（剩餘數、等待人數） | `list[StockItem]` | 每 3 分鐘同步 → `GET /stock` |
| `fetch_centers()` | 各中心介紹頁（可手填常數） | `list[Center]` | `GET /centers` |
| `fetch_center_calendar(center_id, start, days)` | 開館時段 + data.gov.tw 辦公日曆表 + 臨時休館公告 | `list[CalendarDay]` | 行事曆、取貨期限 |
| `forward_reservation(payload)` | 送往中心（介接方式待確認） | `ForwardReceipt` | 送件佇列 |

每個 function 的註解裡寫了：網址、步驟、「網頁上看到的 → 要填的欄位」對照表、注意事項、回傳範例。

寫完後自己檢查格式（在專案根目錄）：

```bash
python -m app.tools.crawlers.check stock     # 或 catalog / centers / calendar / all
```

## 主動推播（FCM）

使用者不用開著 App：預約進度、取貨提醒、到貨、公告都會推播到手機。

| 事件 | 誰觸發 | 多久檢查一次 |
|---|---|---|
| `reservation.booked` / `cancelled` | 使用者建立、取消預約 | 即時 |
| `reservation.pickup_reminder` / `expired` | 排程 | 每 1 分鐘 |
| `reservation.confirmed` / `completed` / `cancelled` | 中心回報（`/hooks/center/status`） | 即時 |
| `stock.arrived` | 庫存同步發現 0 → >0 | 每 `STOCK_SYNC_SECONDS`（預設 3 分鐘） |
| `service.notice` | 官網出現新公告（`fetch_notices`） | 每 `PUSH_CHECK_MINUTES`（預設 5 分鐘），同時重試失敗的推播 |

- App 啟動時 `POST /devices`（Bearer mailbox_key，body `{mailbox_id, platform: "fcm", token}`），
  token 更新時重送；`DELETE /devices?mailbox_id=` 取消（token 放 body）。
- 公告走 FCM topic `assistive-notice`，App 啟動時要訂閱。
- 推播 data：`{type, event_id, reservation_id?, variant_id?}`；文案見 `app/features/notification/texts.py`。
  **鎖定畫面看得到：不放姓名、身分證、電話、輔具名稱。**
- 事件仍會寫進信箱，App 打開時用 `/mailboxes/{id}/events` 補拉，推播漏掉也不會少資料。
- 設定 `FCM_PROJECT_ID`、`FCM_CREDENTIALS_FILE`（Firebase 服務帳號金鑰，不要 commit）才會真的發。

## 設定（app/config.py）

所有設定集中在 `app/config.py`：
- **`.env` 只放幾個特別的**：`HOST`、`PORT`、`TEST_MODE`、`DB_PATH`、`ENABLE_BACKGROUND_JOBS`，以及機密
  `HOOK_SECRET`、`FCM_PROJECT_ID`、`FCM_CREDENTIALS_FILE`（範本見 `.env.example`）。
- **其他直接改 `config.py`**：
  - `API_ENABLED`：每組 API 開或關（關掉的回 404）
  - `SERVICES`：開放哪些服務、要填哪幾組欄位、items 可選項目、最多幾個
  - `FIELDS`：每個欄位的必填 / 長度 / 格式 / 選項 —— `POST /reservations` 的驗證直接讀這裡（`app/tools/fields.py`）
  - `BORROW_CATEGORIES`、`BLOCKED_VARIANTS`：開放借用哪些分類 / 品項（`/catalog`、借用、到貨通知都套用）
  - `FORWARD_TO_CENTER`：要不要送件到中心（目前 False：預約只記錄在本機，不存聯絡資料）
  - 排程間隔、推播 topic、測試模式的模擬變化、CORS…
- `GET /assistive/v1/forms/{service}`：把上面的設定給前端（可選項目、必填欄位、行政區、欄位規則）。

## 測試模式（TEST_MODE）

`.env` 設 `TEST_MODE=true` 後啟動 server（`python app/main.py`）：

- 爬蟲**不連官網**，改用 `app/tools/testdata.py` 的固定假資料：12 類 62 款、3 間中心、行事曆（例假日 / 國定假日 /
  臨時休館 / 補班）、4 則公告。欄位刻意做得變化多（沒圖、規格空、說明很長、名稱很長、庫存 0 / 999…）方便測相容性。
- 開放 `/assistive/v1/_test/*` 測試 API（正式模式回 404），可以直接觸發各種狀態，不用等時間、不用中心系統。
  要同時符合 `config.API_ENABLED["test"] = True` 與 `.env` 的 `TEST_MODE=true`。
- **測試面板**：瀏覽器打開 `http://<HOST>:<PORT>/assistive/v1/_test/panel`（同 Wi-Fi 的隊友也能開）。
  按按鈕直接推送 8 種通知、走真正的預約流程，下方即時顯示推播結果，並寫好「這個結果代表是誰的問題」。
- 沒設定 FCM 也會跑完整推播流程，結果記成 `local`（只記錄在本機）；設定了就真的送到手機。
- `scenario` / `flow` 沒給 `--token` 時會登記本機假裝置（`local-信箱ID`），推播照樣記錄，`outbox` / `watch` 看得到。
- 每一則推播都記錄在本機 DB（`DB_PATH`，預設 `data/local.db`）的 `push_log`。
- **模擬資料變化**（`config.TEST_SIMULATE_CHANGES`）：後端每 3 分鐘抓一次資料，測試模式下每次抓，假資料都會變——
  有人訂閱的缺貨品項會變成有貨（推到貨通知）、每幾次出現一則新公告（推服務公告）。不想等就按面板的「立刻抓一次」
  或 `python -m app.cli sync`。

**正式環境一定要 `TEST_MODE=false`。**

### CLI 推播 / 狀態測試工具

```bash
python -m app.cli --help
```

| 指令 | 需要 server | 做什麼 |
|---|---|---|
| `devices` | | 列出 DB 裡登記的手機 |
| `push --token <token>` / `--mailbox mb_x` / `--all` `[--type ...]` | | 直接推一則通知（預設「預約成功」） |
| `topic --title "..."` | | 推公告到 topic |
| `types` | | 列出 8 種通知與文案 |
| `outbox` / `watch` | | 看推播紀錄 / 即時顯示新推播 |
| `state` | ✓ | 信箱、預約、裝置、最近推播 |
| `scenario --token <token>` | ✓ | 建信箱 + 登記手機 + 借用預約（推「預約成功」） |
| `trigger <預約編號> pickup_reminder\|expired\|confirmed\|completed\|cancelled` | ✓ | 讓預約進入該狀態並推播 |
| `stock <variant_id> <數量>` | ✓ | 設定庫存；0 → >0 推「到貨通知」 |
| `notice "標題"` | ✓ | 發公告 |
| `sync` | ✓ | 立刻抓一次資料（測試模式會模擬官網變化）→ 有變化就推播 |
| `flow --token <token>` | ✓ | 一次跑完：預約成功 → 取貨提醒 → 逾期 |

用手機測：App 拿到 FCM token 後，`python -m app.cli flow --token <token>`，手機應該依序收到三則通知。

## 本機 DB

`app/tools/db.py`（SQLite，Python 內建，不用另外裝），檔案在 `DB_PATH`（預設 `data/local.db`）。
存信箱與事件、預約、Idempotency-Key、到貨訂閱、庫存（含 version）、中心 webhook 去重、推播裝置、推播紀錄；
**全部不含個資**，server 重啟資料都還在。要清空就刪掉 DB 檔。server 和 CLI 讀同一個檔案。

## 開發

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app/main.py        # 或 uvicorn app.main:app --reload
pytest
```

## 尚未完成（TODO）

- 送件到中心：`FORWARD_TO_CENTER = False`，預約只記錄在本機；要送件需先決定介接方式（`forward_reservation`）
- 送件佇列個資的 KMS 加密
- Rate limit（每信箱寫入 ≤ 10 次/分、讀取 ≤ 120 次/分）
