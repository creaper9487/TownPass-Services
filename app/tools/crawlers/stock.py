from app.tools.crawlers.schemas import StockItem


def fetch_stock() -> list[StockItem]:
    """抓取所有品項目前的「剩餘數」與「等待人數」。

    資料來源：
        https://tpap.gov.taipei/app37/rentView/index
        （同 fetch_catalog 的頁面，每個品項旁邊會顯示剩餘數量與等待人數；
         2026-11-07 快照中輪椅全部 0 庫存、等待 6–23 人）

    需要的功能：
        1. 回傳「全部」品項的庫存，不要只回有變動的（後端自己算差異）。
        2. variant_id 必須跟 fetch_catalog() 回傳的一致。
        3. 數字欄位轉成 int；官網顯示「無」或空白時當 0。
        4. 要輕量：後端每 30–60 秒呼叫一次。請勿額外抓圖片或詳細頁。
           （正式上線前需取得中心同意這個抓取頻率）

    回傳：
        list[StockItem]，範例：
        [
            {"variant_id": "101", "stock": 0, "waiting": 23},
            {"variant_id": "205", "stock": 4, "waiting": 0}
        ]
    """
    raise NotImplementedError("fetch_stock 尚未實作")
