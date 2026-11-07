from datetime import date

from app.tools.crawlers.schemas import CalendarDay, CenterId


def fetch_center_calendar(center_id: CenterId, start: date, days: int) -> list[CalendarDay]:
    """【爬什麼】某間中心接下來每一天「有沒有開」、幾點開幾點關。

    為什麼需要：借用預約要在「預約後 2 天內（含當天）」去中心取貨，
    後端要知道這 2 天哪幾天有開，才能告訴使用者哪天可以去拿；取貨提醒也看開關館時間。

    ─────────────────────────────────────────
    參數
        center_id  "heyi" / "south" / "west"
        start      從哪一天開始，例：date(2026, 11, 7)
        days       要幾天，例：14

    ─────────────────────────────────────────
    資料來源（三個合起來算）
        1. 中心每週固定開館時間 → 直接用 fetch_centers() 的 opening_hours
        2. 國定假日、補班日 → 政府資料開放平臺「中華民國政府行政機關辦公日曆表」
           https://data.gov.tw/dataset/14718
           （有 CSV / JSON 可下載；裡面每天會標「是否放假」和假日名稱，例如國慶日）
        3. 臨時休館 → 各中心官網最新消息 / 公告（找不到就先略過）

    ─────────────────────────────────────────
    怎麼算每一天
        a. 這天是國定假日（第 2 點標放假）→ is_open = False，note = 假日名稱
        b. 這天有臨時休館公告           → is_open = False，note = "臨時休館"
        c. 這天的星期幾不在開館時間內   → is_open = False，note = "週日休館" 之類
        d. 補班日：如果中心補班日有開，照平日處理
        e. 其他 → is_open = True，open / close 填當天開館、閉館時間

    ─────────────────────────────────────────
    每一天要填的欄位
        | 欄位     | 型別        | 範例          | 說明                         |
        |----------|-------------|---------------|------------------------------|
        | date     | date        | "2026-11-07"  | 日期                         |
        | is_open  | bool        | true          | 這天有沒有開                 |
        | open     | str / None  | "08:30"       | 開館時間，休館填 None        |
        | close    | str / None  | "17:30"       | 閉館時間，休館填 None        |
        | note     | str / None  | "國慶日"      | 休館原因，一般日子填 None    |

    ─────────────────────────────────────────
    注意
        - 一定要剛好回傳 days 筆，日期從 start 開始一天一天連續，不能跳過休館日。
        - 一天有午休兩段的話，open 填最早開館、close 填最晚閉館。

    ─────────────────────────────────────────
    回傳範例（start=2026-11-07, days=3）
        [
            {"date": "2026-11-07", "is_open": true,  "open": "08:30", "close": "17:30", "note": null},
            {"date": "2026-11-08", "is_open": false, "open": null,    "close": null,    "note": "週日休館"},
            {"date": "2026-11-09", "is_open": true,  "open": "08:30", "close": "17:30", "note": null}
        ]

    檢查：python -m app.tools.crawlers.check calendar
    後端快取 5 分鐘。
    """
    raise NotImplementedError("fetch_center_calendar 尚未實作")
