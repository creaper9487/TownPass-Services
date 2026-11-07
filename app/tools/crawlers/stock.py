"""二手輔具剩餘數量與候補人數。"""

from ._borrow_source import get_borrow_snapshot
from .schemas import StockItem


def fetch_stock() -> list[StockItem]:
    """回傳所有款式的 stock/waiting，variant_id 對應 CatalogVariant.id。

    實測官網首頁只有分類總數，必須 GET 各分類的 vehicleDetail HTML
    才有款式庫存；目前一次完整更新為分類頁 1 次、各分類頁各 1 次。
    不下載照片，不呼叫單品預約、候補或取消網址。
    與目錄共用最長 30 秒的完整快照，後端排程每 3 分鐘呼叫一次（app/config.py 的 STOCK_SYNC_SECONDS）。

    有庫存且顯示預約按鈕時，官網省略候補欄；依 README 將其轉為 0。
    其他無法辨識的數字使整次更新失敗，不以空清單／假 0 覆蓋有效庫存。
    正式高頻使用仍需按 README 與中心確認。
    """
    return [item.model_copy(deep=True) for item in get_borrow_snapshot().stock]
