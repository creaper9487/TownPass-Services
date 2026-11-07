# 輔具預約 API 完整清單

> 基準網址：`http://192.168.88.208:8000/assistive/v1`（後端電腦 IP，換網路會變）
> 互動式文件：`http://192.168.88.208:8000/docs`
> 下面每個回傳範例都是實際呼叫拿到的（測試模式資料，正式模式欄位一樣、品項代碼不同）。
> **這份以外的路徑都不存在**（例如 `/variants/specs`、`/stock/{id}/centers` 會 404，見最後一節）。

## 總覽

| # | 方法 | 路徑 | 驗證 | 用途 |
|---|---|---|---|---|
| 1 | GET | `/health` | | 健康檢查 |
| 2 | GET | `/catalog` | | 分類與款式（名稱、照片、**規格**） |
| 3 | GET | `/stock` | | 所有款式的剩餘數 / 等待人數 |
| 4 | GET | `/stock?since={version}` | | 只拿有變動的款式 |
| 5 | GET | `/centers` | | 3 間中心 |
| 6 | GET | `/centers/{center_id}/calendar` | | 某中心每天有沒有開館 |
| 7 | GET | `/forms/{service}` | | 表單選項、必填欄位、欄位規則 |
| 8 | POST | `/mailboxes` | | 建立匿名信箱 |
| 9 | GET | `/mailboxes/{mailbox_id}/events` | Bearer | 取事件（long-poll） |
| 10 | GET | `/mailboxes/{mailbox_id}/stream` | Bearer | 取事件（SSE） |
| 11 | POST | `/mailboxes/{mailbox_id}/ack` | Bearer | 標記已讀 |
| 12 | POST | `/devices` | Bearer | 登記推播裝置（FCM token） |
| 13 | DELETE | `/devices?mailbox_id=` | Bearer | 取消登記 |
| 14 | POST | `/reservations` | Idempotency-Key | 建立預約 |
| 15 | POST | `/reservations:batchGet` | access_key | 查多筆預約狀態 |
| 16 | POST | `/reservations/{id}:cancel` | access_key | 取消預約 |
| 17 | POST | `/subscriptions` | Bearer | 登記到貨通知 |
| 18 | GET | `/subscriptions?mailbox_id=` | Bearer | 我的到貨通知（含狀態） |
| 19 | DELETE | `/subscriptions/{id}` | Bearer | 取消到貨通知 |
| 20 | POST | `/hooks/center/status` | HMAC 簽章 | （中心系統用）回報預約狀態 |
| 21 | POST | `/hooks/center/stock` | HMAC 簽章 | （中心系統用）回報庫存 |

**驗證方式**
- **Bearer**：Header `Authorization: Bearer <mailbox_key>`（`POST /mailboxes` 拿到的 key，只回一次）。
- **access_key**：放在 body，`POST /reservations` 拿到的，只回一次。
- **Idempotency-Key**：Header，每次「送出」產生一個 UUID，重試用同一個。

**ETag / 304**：`/catalog`、`/centers`、`/centers/{id}/calendar`、`/stock` 回傳 `ETag`；下次帶 `If-None-Match: <ETag>`，沒變就回 **304**（沒有 body）。

**時間**一律 ISO 8601 `+08:00`；日期 `YYYY-MM-DD`；時刻 `HH:MM`。

---

## 錯誤格式（所有 API 一樣）

```json
{ "type": "about:blank", "title": "欄位格式錯誤", "status": 422, "code": "INVALID_FIELD", "fields": ["variant_id"] }
```

| HTTP | code | 意思 | 額外欄位 |
|---|---|---|---|
| 401 | `BAD_KEY` | mailbox_key / access_key 不對或沒帶 | |
| 404 | `NOT_FOUND` | 找不到（或路徑不存在，此時是 FastAPI 預設的 `{"detail":"Not Found"}`） | |
| 409 | `OUT_OF_STOCK` | 借用時沒庫存 | `stock`、`waiting`（直接更新畫面） |
| 409 | `DUPLICATE_WAITLIST` | 同一類已經有等待中的到貨通知 | |
| 409 | `IDEMPOTENCY_CONFLICT` | 同一個 Idempotency-Key 送了不同內容 | |
| 422 | `INVALID_FIELD` | 欄位錯誤（品項不存在、格式不對、少欄位…） | `fields`：哪幾個欄位（不回顯你填的值） |
| 422 | `PICKUP_WINDOW_CLOSED` | 取貨期限內中心沒開館（目前 config 關閉開館檢查，不會出現） | |
| 422 | `NOT_ELIGIBLE` | 居住地不在臺北市 | |
| 501 | `NOT_IMPLEMENTED` | 該資料的爬蟲還沒寫好 | |
| 503 | `SOURCE_UNAVAILABLE` | 官網資料暫時抓不到 | |

---

## 1. GET /health
```json
{ "status": "ok" }
```

## 2. GET /catalog
分類與款式。**規格在這裡**（`specs`、`attrs`），沒有另外的規格 API。
`Cache-Control: max-age=3600`；官網抓不到時回上一次成功的資料。

```json
{
  "categories": [
    {
      "id": "1",
      "name": "輪椅類",
      "image": "https://…/c1.jpg",
      "variants": [
        {
          "id": "182",                       // ★ 款式代碼 = variant_id，所有 API 都用這個
          "name": "輕量型輪椅",
          "image": "https://…/182.jpg",      // 可能是 null
          "specs": ["座寬 18 吋", "重量 15 公斤"],   // 可能是 []
          "description": "適合短距離移動。",  // 可能是 null
          "attrs": {                          // 可能是 null；各欄位也可能是 null
            "height_min": null,               // 適用身高下限（公分）
            "height_max": null,               // 適用身高上限（公分）
            "seat_width_in": 18.0,            // 座寬（英吋）
            "weight_max_kg": 100.0            // 最大承重（公斤）
          }
        }
      ]
    }
  ]
}
```

## 3. GET /stock
所有款式的**總**庫存（不分中心）。
```json
{
  "version": 62,                                  // 每次有變動就 +1
  "as_of": "2026-11-07T19:06:56.454556+08:00",
  "items": {
    "181": { "stock": 0,  "waiting": 3 },         // key = variant_id
    "182": { "stock": 1,  "waiting": 0 },
    "183": { "stock": 12, "waiting": 0 }
  }
}
```

## 4. GET /stock?since={version}
只回 `version` 之後有變動的款式（格式同上，`items` 只有變動的）；**沒有變動回 304**。
頁面開著時每 10 秒問一次，`since` 帶上次拿到的 `version`。

## 5. GET /centers
```json
{
  "centers": [
    {
      "id": "heyi",                               // heyi / south / west
      "name": "臺北市合宜輔具中心",
      "address": "臺北市中山區玉門街1號",
      "phone": "02-77137760",
      "districts": ["中山區", "大同區", "士林區", "北投區"],
      "open_days": [2, 3, 4, 5, 6],               // 1=星期一 … 7=星期日
      "hours": [ { "from": "09:00", "to": "12:00" }, { "from": "13:30", "to": "17:00" } ],
      "lat": 25.0701455,
      "lng": 121.5217556
    }
  ]
}
```

## 6. GET /centers/{center_id}/calendar?from=YYYY-MM-DD&days=14
`from` 不給 = 今天；`days` 1～60，預設 14。
```json
{
  "center_id": "heyi",
  "days": [
    { "date": "2026-11-07", "open": true,  "hours": [ { "from": "09:00", "to": "12:00" }, { "from": "13:30", "to": "17:00" } ], "reason": null },
    { "date": "2026-11-08", "open": false, "hours": [], "reason": "例假日休館" }
  ]
}
```

## 7. GET /forms/{service}
`service`：`borrow` / `assess` / `repair` / `recycle`。表單照這個畫，不要寫死選項。
```json
{
  "service": "repair",
  "label": "輔具維修",
  "item_options": ["居家用照顧床(病床)", "氣墊床", "輪椅座墊", "手動輪椅", "電動輪椅", "拐杖/助行器", "便盆椅", "其他"],
  "allow_other": true,          // 選「其他」時 other_text 必填
  "max_items": 8,
  "required_fields": ["items", "contact.name", "contact.mobile", "contact.gender",
                      "subject.name", "subject.id_no", "subject.registered_district",
                      "subject.living_county", "subject.living_district"],
  "districts": ["中正區", "大同區", "中山區", "松山區", "大安區", "萬華區",
                "信義區", "士林區", "北投區", "內湖區", "南港區", "文山區"],
  "fields": {
    "contact.name":   { "required": true, "min_length": 1, "max_length": 50, "label": "聯絡人姓名" },
    "contact.mobile": { "required": true, "pattern": "^09\\d{8}$", "label": "手機" }
    // …每個欄位的規則
  }
}
```
`borrow` 的 `item_options` 是 `[]`（借用的 items 是 `variant_id`）。

## 8. POST /mailboxes
無 body。
```json
201 { "mailbox_id": "mb_jyHgi2k-JpOx", "mailbox_key": "W7QRwSbl8j…" }   // key 只回這一次
```

## 9. GET /mailboxes/{mailbox_id}/events?cursor=0&wait=25
Bearer。`cursor` = 上次的 `next_cursor`（第一次 0）；`wait` 0～25 秒，有新事件就立刻回。
```json
{
  "events": [
    {
      "cursor": 1,
      "id": "ev_XN39r_qV2OvF",
      "type": "reservation.booked",
      "ts": "2026-11-07T19:06:56.500797+08:00",
      "ref": { "reservation_id": "B202611078396" },
      "data": { "pickup_deadline": "2026-11-08", "pickup_dates": ["2026-11-07", "2026-11-08"] },
      "expires_at": "2026-12-07T19:06:56.500797+08:00"
    }
  ],
  "next_cursor": 1
}
```
事件類型：
| type | ref | data |
|---|---|---|
| `reservation.booked` | `reservation_id` | `pickup_deadline`、`pickup_dates` |
| `reservation.pickup_reminder` | `reservation_id` | `pickup_deadline` |
| `reservation.expired` | `reservation_id` | |
| `reservation.confirmed` / `completed` / `cancelled` | `reservation_id` | |
| `stock.arrived` | `variant_id`、`subscription_id` | `variant_name`、`category_name`（目錄查不到時為 null） |
| `service.notice` | | `notice_id`、`title`、`center_ids` |

## 10. GET /mailboxes/{mailbox_id}/stream
Bearer；Header `Last-Event-ID` = cursor。`text/event-stream`，每筆：
```
id: 1
event: reservation.booked
data: { …同上的事件物件… }
```
沒事件時每 25 秒送 `: keep-alive`。⚠ 瀏覽器 `EventSource` 不能帶 Authorization header，網頁請用 9 或透過 Flutter。

## 11. POST /mailboxes/{mailbox_id}/ack
Bearer。Body `{ "cursor": 1 }` → **204**（cursor 以前的事件會被刪掉）。

## 12. POST /devices
Bearer。同一個 token 重送 = 更新。
```json
{ "mailbox_id": "mb_xxx", "platform": "fcm", "token": "<FCM token>" }
```
→ **204**

## 13. DELETE /devices?mailbox_id=mb_xxx
Bearer。Body `{ "token": "<FCM token>" }` → **204**

## 14. POST /reservations
Header `Idempotency-Key`（必填）。
```json
{
  "service": "borrow",                  // borrow / assess / repair / recycle
  "mailbox_id": "mb_xxx",
  "center_id": "heyi",                  // 只有 borrow 要
  "items": ["182"],                     // borrow：variant_id；其他：/forms 的 item_options
  "other_text": null,                   // items 有「其他」時必填
  "contact": { "name": "王小明", "mobile": "0912345678", "phone": null, "gender": "M", "email": null },
  "subject": null,                      // assess / repair 必填：{name, id_no, registered_district, living_county, living_district, remark}
  "pickup":  null                       // recycle 必填：{district, address, has_elevator, need_certificate, remark}
}
```
借用：
```json
201 { "id": "B202611078396", "access_key": "UL6SGdYy…", "status": "booked",
      "pickup": { "deadline": "2026-11-08", "open_dates": ["2026-11-07", "2026-11-08"] } }
```
評估 / 維修 / 回收：
```json
201 { "id": "R202611072077", "access_key": "n2NyKmNr…", "status": "submitted", "pickup": null }
```
`access_key` 只回這一次。錯誤：`OUT_OF_STOCK`、`INVALID_FIELD`、`NOT_ELIGIBLE`、`IDEMPOTENCY_CONFLICT`。

## 15. POST /reservations:batchGet
Body 是陣列（最多 50 筆）：
```json
[ { "id": "B202611078396", "access_key": "UL6SGdYy…" }, { "id": "B000", "access_key": "x" } ]
```
```json
200 [
  { "id": "B202611078396", "status": "booked", "version": 1,
    "updated_at": "2026-11-07T19:06:56.500636+08:00",
    "pickup": { "deadline": "2026-11-08", "open_dates": ["2026-11-07", "2026-11-08"] } },
  { "id": "B000", "error": "BAD_KEY" }
]
```
`status`：`booked`（借用已預約）/ `submitted`（已送出）/ `confirmed` / `completed` / `cancelled` / `expired`（逾期）。

## 16. POST /reservations/{id}:cancel
Body `{ "access_key": "…" }`；重複呼叫結果一樣（借用會釋回庫存）。
```json
200 { "id": "B202611078396", "status": "cancelled", "version": 2 }
```

## 17. POST /subscriptions
Bearer。同一類「等待中」最多 1 筆。
```json
{ "mailbox_id": "mb_xxx", "variant_id": "181" }
```
```json
201 { "id": "sub_tPZHOROR9GgL" }
```
錯誤：`DUPLICATE_WAITLIST`、`INVALID_FIELD`（品項不存在 / 不開放）。

## 18. GET /subscriptions?mailbox_id=mb_xxx
Bearer。
```json
200 [
  { "id": "sub_tPZHOROR9GgL", "variant_id": "181", "variant_name": "一般型輪椅",
    "category_id": "1", "category_name": "輪椅類",       // 名稱是訂閱當下從目錄查到的，可能是 null
    "status": "waiting",                              // waiting 等待中 / arrived 已到貨
    "created_at": "2026-11-07T19:06:56.519670+08:00",
    "arrived_at": null }                              // 到貨時間
]
```

## 19. DELETE /subscriptions/{id}
Bearer → **204**

## 20–21. POST /hooks/center/status、/hooks/center/stock
中心系統用，前端不用管。Header `X-Timestamp`（unix 秒）、`X-Signature`（HMAC-SHA256）。
- status：`{ event_id, reservation_id, status: confirmed|completed|cancelled, occurred_at }` → 204
- stock：`{ event_id, variant_id, stock, waiting }` → 204

---

## 推播（FCM）
App 用 `POST /devices` 登記後，每個事件都會推一則：
```
notification: { title, body }                         // 鎖定畫面看得到，不含姓名 / 電話 / 輔具名稱
data: { type, event_id, reservation_id?, variant_id?, variant_name?, category_name? } // 全部是字串
```
到貨通知（`stock.arrived`）的 `data` 帶 `variant_name`、`category_name`，`notification.body` 也會顯示品項名稱。
公告（`service.notice`）推到 topic `assistive-notice`。文案見 `docs/FRONTEND.md` 2.3。

---

## 不存在的路徑（前端目前有打，會 404）

| 前端打的 | 說明 | 改用 |
|---|---|---|
| `GET /variants/specs` | 沒有這個 API | 規格在 `GET /catalog` 每一款的 `specs`、`attrs` |
| `GET /stock/{variant_id}/centers` | 後端**沒有分中心的庫存**，只有總庫存 | `GET /stock` 的 `items[variant_id]`；要分中心需要爬蟲先確認官網有沒有這份資料 |

---

## 測試模式專用（`TEST_MODE=true` 才有，正式模式 404）
`/_test/state`、`/_test/scenario`、`/_test/reservations/{id}/trigger`、`/_test/stock`、`/_test/notices`、
`/_test/devices`、`/_test/push`、`/_test/events`、`/_test/sync`、`/_test/panel`（測試面板網頁）。前端正式功能不要用。
