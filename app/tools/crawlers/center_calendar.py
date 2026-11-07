from datetime import date

from app.tools.crawlers.schemas import CalendarDay, CenterId


def fetch_center_calendar(center_id: CenterId, start: date, days: int) -> list[CalendarDay]:
    """【爬什麼】某間中心接下來每一天「有沒有開」、開哪些時段。

    為什麼需要：借用預約要在「預約後 2 天內（含當天）」去中心取貨，
    後端要知道這 2 天哪幾天有開，才能告訴使用者哪天可以去拿；取貨提醒也看開關館時間。

    ─────────────────────────────────────────
    參數
        center_id  "heyi" / "south" / "west"
        start      從哪一天開始，例：date(2026, 11, 7)
        days       要幾天，例：14

    ─────────────────────────────────────────
    資料來源（三個合起來算）
        1. 中心每週固定開館日與時段 → 直接用 fetch_centers() 的 open_days、hours
        2. 國定假日、補班日 → 政府資料開放平臺「中華民國政府行政機關辦公日曆表」
           https://data.gov.tw/dataset/14718
           （有 CSV / JSON 可下載；每天會標「是否放假」和假日名稱，例如國慶日）
        3. 臨時休館 → 各中心官網最新消息 / 公告（找不到就先略過）

    ─────────────────────────────────────────
    怎麼算每一天
        a. 國定假日（第 2 點標放假）        → open=False, hours=[], reason=假日名稱
        b. 有臨時休館公告                    → open=False, hours=[], reason="臨時休館"
        c. 星期幾不在 open_days 裡           → open=False, hours=[], reason="例假日休館"
        d. 補班日：中心補班日有開的話照平日處理
        e. 其他                              → open=True,  hours=當天開館時段, reason=None

    ─────────────────────────────────────────
    每一天要填的欄位
        | 欄位    | 型別         | 範例                                  | 說明                    |
        |---------|--------------|---------------------------------------|-------------------------|
        | date    | date         | "2026-11-07"                          | 日期                    |
        | open    | bool         | true                                  | 這天有沒有開            |
        | hours   | list         | [{"from":"08:30","to":"17:30"}]       | 開館時段，休館填 []     |
        | reason  | str / None   | "國慶日"                              | 休館原因，開館日填 None |

    ─────────────────────────────────────────
    注意
        - 一定要剛好回傳 days 筆，日期從 start 開始一天一天連續，休館日也要放。
        - 時間一律 "HH:MM"。

    ─────────────────────────────────────────
    回傳範例（start=2026-11-07, days=3）
        [
            {"date": "2026-11-07", "open": true,  "hours": [{"from": "08:30", "to": "17:30"}], "reason": null},
            {"date": "2026-11-08", "open": false, "hours": [], "reason": "例假日休館"},
            {"date": "2026-11-09", "open": true,  "hours": [{"from": "08:30", "to": "17:30"}], "reason": null}
        ]

    檢查：python -m app.tools.crawlers.check calendar
    後端快取 5 分鐘。
    """
    # ── 範本 ──
    # from datetime import timedelta
    # from app.tools.crawlers.centers import fetch_centers
    #
    # center = next(c for c in fetch_centers() if c.id == center_id)
    # holidays = load_holidays()        # ← 自己寫：讀 data.gov.tw 辦公日曆表 → {date: "國慶日", ...}
    # closures = load_closures(center_id)  # ← 自己寫：臨時休館 → {date: "臨時休館"}；沒有就回 {}
    #
    # result = []
    # for i in range(days):
    #     d = start + timedelta(days=i)
    #     if d in holidays:
    #         result.append(CalendarDay(date=d, open=False, hours=[], reason=holidays[d]))
    #     elif d in closures:
    #         result.append(CalendarDay(date=d, open=False, hours=[], reason=closures[d]))
    #     elif d.isoweekday() not in center.open_days:     # isoweekday(): 1=星期一 … 7=星期日
    #         result.append(CalendarDay(date=d, open=False, hours=[], reason="例假日休館"))
    #     else:
    #         result.append(CalendarDay(date=d, open=True, hours=center.hours, reason=None))
    # return result
    raise NotImplementedError("fetch_center_calendar 尚未實作")
