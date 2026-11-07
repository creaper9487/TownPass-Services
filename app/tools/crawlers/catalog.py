"""二手輔具借用目錄，沿用官網分類與款式代碼。"""

from ._borrow_source import get_borrow_snapshot
from .schemas import CatalogCategory


def fetch_catalog() -> list[CatalogCategory]:
    """取得全部借用款式、圖片網址、規格與明確的數值屬性。

    官網分類在 /rentView/additem，款式在 /rentView/vehicleDetail/{id}。
    僅讀取公開 HTML，不下載圖片、不進入預約或候補申請頁。
    與 fetch_stock 共用 process 內最長 30 秒的完整快照；外層目錄快取仍由後端管理。
    網路或解析失敗會拋出例外，不回傳誤導性的空目錄。
    """
    return [category.model_copy(deep=True) for category in get_borrow_snapshot().catalog]
