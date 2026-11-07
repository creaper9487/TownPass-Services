from datetime import date

from app.tools.crawlers.schemas import CalendarDay, CenterId


def fetch_center_calendar(center_id: CenterId, start: date, days: int) -> list[CalendarDay]:
    """取得某中心從 start 起連續 days 天，每天是否開館。

    用途：
        借用預約要在「預約後 2 天內（含當日）」取貨，後端用這個算出取貨期限內有哪些開館日；
        取貨提醒也依當天開館 / 閉館時間發送。

    資料來源（需要組合）：
        1. 中心每週固定開館時段（同 fetch_centers 的 opening_hours）。
        2. 國定假日 / 補班：政府資料開放平臺「中華民國政府行政機關辦公日曆表」
           https://data.gov.tw/dataset/14718 （有 CSV / JSON）
        3. 臨時休館：各中心官網公告（沒有就先略過）。

    需要的功能：
        1. 回傳剛好 days 筆，日期從 start 開始連續、不可跳號。
        2. 每筆標示 is_open；開館日填當天 open / close（HH:MM），休館日填 None。
        3. note 寫休館原因（例：「國慶日」「臨時休館」），一般日子 None。
        4. center_id 只會是 "heyi" / "south" / "west"。

    回傳：
        list[CalendarDay]，範例（start=2026-11-07, days=3）：
        [
            {"date": "2026-11-07", "is_open": true,  "open": "08:30", "close": "17:30", "note": null},
            {"date": "2026-11-08", "is_open": false, "open": null,    "close": null,    "note": "週日休館"},
            {"date": "2026-11-09", "is_open": true,  "open": "08:30", "close": "17:30", "note": null}
        ]

    呼叫頻率：後端快取 5 分鐘。
    """
    raise NotImplementedError("fetch_center_calendar 尚未實作")
