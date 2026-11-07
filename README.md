# taipei-codefest-2026-Backend

臺北市輔具預約後端（FastAPI），只服務臺北市 12 個行政區。API 基準路徑 `/assistive/v1`，啟動後看 http://127.0.0.1:8000/docs

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

## 開發

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app/main.py        # 或 uvicorn app.main:app --reload
pytest
```

## 尚未完成（TODO）

- 資料庫：目前全在記憶體，重啟即消失（換 DB 只改各 feature 的 repository.py）
- 送件佇列個資的 KMS 加密
- Rate limit（每信箱寫入 ≤ 10 次/分、讀取 ≤ 120 次/分）
