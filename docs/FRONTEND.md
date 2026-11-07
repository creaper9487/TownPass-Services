# 輔具預約：前端串接說明

> 給 Flutter（台北通 App）與網頁前端。後端最新版在 `developer` 分支。
> 有問題先開測試面板看推播結果（第 5 節），通常就知道是哪一端的問題。

## 0. 基本資訊

| 項目 | 值 |
|---|---|
| 基準網址 | `http://192.168.88.208:8000/assistive/v1`（後端電腦的 IP，換網路會變，問後端） |
| API 文件 | `http://192.168.88.208:8000/docs` |
| 測試面板 | `http://192.168.88.208:8000/assistive/v1/_test/panel`（後端開測試模式時才有） |
| 格式 | JSON、UTF-8；時間一律 ISO 8601 `+08:00` |
| CORS | 全開，網頁可以直接打 |
| Firebase 專案 | `taipei-townpass-2026-11`（App 一定要用這個，後端推播用同一個） |

**錯誤格式**（所有 API 一樣）：
```json
{ "status": 422, "code": "INVALID_FIELD", "title": "欄位格式錯誤", "fields": ["contact.mobile"] }
```
| HTTP | code | 意思 |
|---|---|---|
| 401 | `BAD_KEY` | mailbox_key 或 access_key 不對 |
| 404 | `NOT_FOUND` | 找不到 |
| 409 | `OUT_OF_STOCK` | 借用時沒庫存（附 `stock`、`waiting`，直接更新畫面） |
| 409 | `DUPLICATE_WAITLIST` | 同一類已經有等待中的到貨通知 |
| 409 | `IDEMPOTENCY_CONFLICT` | 同一個 Idempotency-Key 送了不同內容 |
| 422 | `INVALID_FIELD` | 欄位錯誤；`fields` 列出哪幾個欄位（不會回顯你填的值） |
| 422 | `PICKUP_WINDOW_CLOSED` | 該中心取貨期限內沒有開館日，請換中心 |
| 422 | `NOT_ELIGIBLE` | 居住地不在臺北市 |

---

## 1. 誰負責什麼

```
Flutter（App）                                網頁（WebView）
─────────────────────────────                 ─────────────────────────────
• 建立信箱、保管 mailbox_key（secure storage） • 只拿 mailbox_id（不碰 mailbox_key）
• Firebase：權限、token、訂閱 topic           • 目錄、庫存、中心、行事曆、表單（公開 API）
• POST /devices 登記手機                       • 建立 / 查詢 / 取消預約（access_key 網頁自己存）
• 到貨通知的新增 / 取消 / 列表（要 key）        • 到貨通知按鈕 → 透過訊息請 Flutter 處理
• 點推播 → 開對應頁面
```

網頁 ↔ Flutter 訊息（名稱已定）：

| 訊息 | 網頁送出 | Flutter 回傳 |
|---|---|---|
| `assistive_mailbox` | （無） | `{ mailbox_id }`；第一次會先 `POST /mailboxes` |
| `assistive_subscribe` | `{ variant_id, on }` | `true` / `false`；`on=false` 是取消 |
| `assistive_subscriptions` | （無） | `GET /subscriptions` 的結果（陣列，見 2.4） |

---

## 2. Flutter（App）要做的

### 2.1 Firebase
```bash
dart pub global activate flutterfire_cli
flutterfire configure        # 選 taipei-townpass-2026-11，勾 Android / iOS
flutter pub add firebase_core firebase_messaging flutter_local_notifications flutter_secure_storage
```

### 2.2 App 啟動時
```dart
await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
final fm = FirebaseMessaging.instance;

await fm.requestPermission();                    // Android 13+、iOS 必須
await fm.subscribeToTopic('assistive-notice');   // 服務公告走 topic

final mailbox = await ensureMailbox();           // 見下方
final token = await fm.getToken();
await registerDevice(mailbox, token!);           // POST /devices
fm.onTokenRefresh.listen((t) => registerDevice(mailbox, t));
```

**ensureMailbox()**：secure storage 沒有就建立一個，有就沿用
```
POST /mailboxes            （無 body）
→ 201 { "mailbox_id": "mb_xxx", "mailbox_key": "xxxx" }
```
⚠ `mailbox_key` **只會回這一次**，存進 secure storage，**不要給網頁**。弄丟就只能重建信箱（舊的通知、訂閱都找不回來）。

**registerDevice()**：登記這支手機（同一個 token 重送 = 更新）
```
POST /devices
Authorization: Bearer <mailbox_key>
{ "mailbox_id": "mb_xxx", "platform": "fcm", "token": "<FCM token>" }
→ 204
```
**沒有做這一步，後端就不知道要推給哪支手機**（到貨、預約通知都會推不到）。

取消登記（登出 / 關閉通知時）：
```
DELETE /devices?mailbox_id=mb_xxx
Authorization: Bearer <mailbox_key>
{ "token": "<FCM token>" }
→ 204
```

### 2.3 收推播
推播內容（後端組好，鎖定畫面看得到，所以**不含姓名、電話、輔具名稱**）：
```json
notification: { "title": "到貨通知", "body": "你訂閱的輔具已到貨，可以預約了" }
data: { "type": "stock.arrived", "event_id": "ev_xxx", "variant_id": "181" }
data: { "type": "reservation.booked", "event_id": "ev_xxx", "reservation_id": "B202611070001" }
```
`data` 的值全部是字串；`reservation_id`、`variant_id` 有的才會出現。

| type | 標題 | 內容 |
|---|---|---|
| `reservation.booked` | 預約成功 | 請於 11/8（日） 前到合宜輔具中心取貨 |
| `reservation.pickup_reminder` | 取貨提醒 | 預約將於 11/8（日） 到期，請記得取貨 |
| `reservation.expired` | 預約已逾期 | 預約已自動取消 |
| `reservation.confirmed` | 中心已確認 | 合宜輔具中心已確認你的申請 |
| `reservation.completed` | 服務已完成 | 你的申請已辦理完成 |
| `reservation.cancelled` | 預約已取消 | 這筆預約已取消 |
| `stock.arrived` | 到貨通知 | 你訂閱的輔具已到貨，可以預約了 |
| `service.notice` | 服務公告 | （公告標題） |

- **App 在背景 / 關閉**：系統自動顯示通知。
- **App 在前景**：Android 預設**不會**顯示，要在 `FirebaseMessaging.onMessage` 裡用 `flutter_local_notifications` 自己顯示。
- **點通知**（`onMessageOpenedApp` / `getInitialMessage`）：
  - `data.reservation_id` 有值 → 開 `/assistive/reservations/{reservation_id}`
  - 其他（到貨、公告）→ 開 `/assistive`

### 2.4 到貨通知（處理網頁送來的訊息）
```
新增   POST /subscriptions                 Authorization: Bearer <mailbox_key>
       { "mailbox_id": "mb_xxx", "variant_id": "181" }
       → 201 { "id": "sub_xxx" }
       → 409 DUPLICATE_WAITLIST（同一類已經有等待中的）
       → 422 INVALID_FIELD（品項不存在或不開放）

列表   GET /subscriptions?mailbox_id=mb_xxx  Authorization: Bearer <mailbox_key>
       → 200 [ { "id": "sub_xxx", "variant_id": "181", "category_id": "1",
                 "status": "waiting" | "arrived",
                 "created_at": "...", "arrived_at": "..." | null } ]

取消   DELETE /subscriptions/{id}            Authorization: Bearer <mailbox_key>
       → 204
```
`assistive_subscribe { variant_id, on:false }`：先 `GET /subscriptions` 找出該 `variant_id` 的 `id`，再 `DELETE`。

### 2.5（選用）App 打開時補拉
推播不保證 100% 送達。App 回到前景時可以補拉一次，有漏的就更新畫面：
```
GET /mailboxes/{mailbox_id}/events?cursor=<上次的 next_cursor>&wait=0
Authorization: Bearer <mailbox_key>
→ { "events": [ { "cursor": 1, "id": "ev_xxx", "type": "reservation.booked", "ts": "...",
                  "ref": { "reservation_id": "B..." }, "data": { ... }, "expires_at": "..." } ],
    "next_cursor": 1 }
```
`next_cursor` 存起來下次帶；處理完可以 `POST /mailboxes/{id}/ack { "cursor": n }` 讓後端清掉。

---

## 3. 網頁要做的

### 3.1 公開資料（不用 key）
| API | 用途 | 備註 |
|---|---|---|
| `GET /catalog` | 分類與款式（名稱、照片、規格） | **款式 `id` 就是 `variant_id`，全部 API 都用這個** |
| `GET /stock` | 每款剩餘數 / 等待人數 | `{version, as_of, items: { "181": {stock, waiting} }}` |
| `GET /stock?since=<version>` | 只拿有變動的 | 頁面開著時每 10 秒一次；沒變動回 **304** |
| `GET /centers` | 3 間中心（地址、電話、時段、座標） | 「離我最近」前端用座標自己算 |
| `GET /centers/{id}/calendar?from=YYYY-MM-DD&days=14` | 每天有沒有開館 | `{date, open, hours[{from,to}], reason}` |
| `GET /forms/{service}` | 評估 / 維修 / 回收表單的可選項目、必填欄位、行政區 | **不要把選項寫死，用這個畫表單** |

`/catalog`、`/centers`、`/stock` 支援 `If-None-Match`（帶上次的 `ETag`，沒變回 304）。

### 3.2 建立預約
```
POST /reservations
Idempotency-Key: <每次「送出」產生一個 UUID；重試時用同一個>
{
  "service": "borrow",                       // borrow / assess / repair / recycle
  "mailbox_id": "mb_xxx",                    // 從 Flutter 的 assistive_mailbox 拿
  "center_id": "heyi",                       // 只有 borrow 要；heyi / south / west
  "items": ["181"],                          // borrow：variant_id；其他：/forms 的 item_options
  "other_text": null,                        // items 有「其他」時必填
  "contact": { "name": "王小明", "mobile": "0912345678", "phone": null,
               "gender": "M", "email": null },  // gender：M / F / X
  "subject": { ... },                        // 只有 assess、repair（欄位見 /forms）
  "pickup":  { ... }                         // 只有 recycle（欄位見 /forms）
}
→ 201 { "id": "B202611070001", "access_key": "xxxx", "status": "booked",
        "pickup": { "deadline": "2026-11-08", "open_dates": ["2026-11-07"] } }
```
- `status`：借用是 `booked`，其他服務是 `submitted`。
- **`id` 和 `access_key` 網頁自己存**（localStorage），之後查詢、取消要用；`access_key` 只回這一次。
- 欄位規則（必填、長度、格式）以 `GET /forms/{service}` 的 `fields` 為準。

### 3.3 我的預約、取消
```
POST /reservations:batchGet
[ { "id": "B...", "access_key": "..." }, ... ]
→ [ { "id": "B...", "status": "booked", "version": 1, "updated_at": "...", "pickup": {...} },
    { "id": "B...", "error": "BAD_KEY" } ]

POST /reservations/{id}:cancel
{ "access_key": "..." }
→ 200 { "id": "B...", "status": "cancelled", "version": 2 }     // 重複呼叫結果一樣
```

### 3.4 到貨通知按鈕
- 缺貨（`stock == 0`）的款式顯示「到貨通知」按鈕 → 送 `assistive_subscribe { variant_id, on: true }` 給 Flutter。
- 「我的到貨通知」列表 → 送 `assistive_subscriptions` 給 Flutter，用回傳的 `status` 顯示「等待中 / 已到貨」。
- **⚠ 現在畫面上的到貨通知（登記編號 `NMW...`）是前端自己的模擬資料，後端沒有收到。** 請改成走上面的流程，
  後端的訂閱編號會是 `sub_...`。

---

## 4. 後端怎麼推（給你們理解用）

```
到貨：後端每 3 分鐘抓一次庫存
      → 「等待中」的訂閱、品項有貨了 → 訂閱 status 改成 arrived
      → 寫進那個人的信箱 → 推播到那個信箱 POST /devices 登記過的手機（不是廣播）
預約：建立 / 取消 / 取貨期限當天 / 逾期自動取消 → 同上，推給那個人
公告：推到 topic assistive-notice → 所有訂閱 topic 的 App
```

---

## 5. 測試方式（不用等 3 分鐘）

後端開測試模式（`TEST_MODE=true`）時：

1. 瀏覽器開 **測試面板** `http://192.168.88.208:8000/assistive/v1/_test/panel`
2. ① 貼上 App 印出的 FCM token → 登記
3. ② 每種通知一個按鈕，按了直接推 → 看手機有沒有跳
4. ④ 「先訂閱一個缺貨品項」→「立刻抓一次」→ 應該收到到貨通知
5. ⑤ 看結果判斷是誰的問題：

| 結果 | 意思 |
|---|---|
| `ok` 但手機沒跳 | **App 端**：通知權限、前景沒處理、token 是舊的 |
| `invalid_token` | **App 端**：token 過期或不是 `taipei-townpass-2026-11` 專案的 |
| `failed` | **後端**：Firebase 金鑰設定 |
| `local` | 推給測試用假裝置，或後端沒設定 Firebase |
| 沒有新紀錄 | 那個信箱沒有登記手機（沒做 `POST /devices`），或後端沒觸發 |

⚠ 測試模式的目錄、庫存是**假資料**（款式代碼 181～242），跟官網真實資料不同。串接時品項代碼一律用 `GET /catalog` 拿到的。

---

## 6. 檢查清單

**Flutter**
- [ ] `flutterfire configure` 選 `taipei-townpass-2026-11`
- [ ] 啟動：`requestPermission()`、`subscribeToTopic('assistive-notice')`
- [ ] 建信箱，`mailbox_key` 存 secure storage
- [ ] `getToken()` → `POST /devices`；`onTokenRefresh` 重送
- [ ] 前景用 `flutter_local_notifications` 顯示
- [ ] 點通知依 `reservation_id` 開頁面
- [ ] 實作 `assistive_mailbox`、`assistive_subscribe`、`assistive_subscriptions`
- [ ] 測試面板 ② 按鈕，手機收得到

**網頁**
- [ ] 品項、庫存、中心、行事曆改打後端 API（不要用模擬資料）
- [ ] 評估 / 維修 / 回收表單用 `GET /forms/{service}` 畫
- [ ] 建立預約帶 `Idempotency-Key`；`id` + `access_key` 存起來
- [ ] 我的預約用 `:batchGet`；取消用 `:cancel`
- [ ] 到貨通知改走 Flutter 訊息（`assistive_subscribe` / `assistive_subscriptions`）
- [ ] 錯誤依 `code` 顯示（`OUT_OF_STOCK` 直接用回傳的 `stock` 更新畫面）
