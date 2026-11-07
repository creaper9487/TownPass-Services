"""爬蟲回傳格式（契約）。爬蟲組只要讓回傳值符合這裡的欄位即可。

ID 規則：
- category_id / variant_id：用官網上的原始代碼（例如 option value、URL 參數）轉成字串；
  一定要「穩定」，同一個品項每次爬都要得到同一個 ID，因為庫存、訂閱都靠它對應。
- center_id：固定為 "heyi"（合宜）/ "south"（南區）/ "west"（西區）。
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

CenterId = Literal["heyi", "south", "west"]


# ---------- 品項目錄 fetch_catalog() ----------
class CatalogVariant(BaseModel):
    """一種輔具（例如「一般型輪椅」）。官網共 62 種。"""

    variant_id: str = Field(..., description="品項代碼，穩定不變")
    category_id: str = Field(..., description="所屬類別代碼")
    name: str = Field(..., description="品項名稱，例：一般型輪椅")
    photo_url: str | None = Field(None, description="照片絕對網址")
    spec: str | None = Field(None, description="規格文字（尺寸、重量等）")
    description: str | None = Field(None, description="說明 / 注意事項")


class CatalogCategory(BaseModel):
    """一個類別（例如「輪椅類」）。官網共 12 類。"""

    category_id: str = Field(..., description="類別代碼，穩定不變")
    name: str = Field(..., description="類別名稱，例：輪椅類")
    variants: list[CatalogVariant] = Field(default_factory=list)


# ---------- 庫存 fetch_stock() ----------
class StockItem(BaseModel):
    """某一種輔具目前的剩餘數與等待人數。"""

    variant_id: str = Field(..., description="對應 CatalogVariant.variant_id")
    stock: int = Field(..., ge=0, description="剩餘可借數量")
    waiting: int = Field(..., ge=0, description="等待（候補）人數")


# ---------- 服務中心 fetch_centers() ----------
class OpeningHours(BaseModel):
    """每週固定開館時段。一天有多段（例如午休）就放多筆。"""

    weekday: int = Field(..., ge=0, le=6, description="0=星期一 … 6=星期日")
    open: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="開館時間 HH:MM")
    close: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="閉館時間 HH:MM")


class Center(BaseModel):
    center_id: CenterId
    name: str = Field(..., description="例：臺北市合宜輔具中心")
    address: str
    phone: str
    districts: list[str] = Field(..., description="負責的行政區，例：['中山區','大同區','士林區','北投區']")
    opening_hours: list[OpeningHours]
    lat: float = Field(..., description="約略緯度（前端算最近中心用）")
    lng: float = Field(..., description="約略經度")


# ---------- 開館行事曆 fetch_center_calendar() ----------
class CalendarDay(BaseModel):
    """某中心某一天是否開館（已考慮國定假日、臨時休館）。"""

    date: date
    is_open: bool
    open: str | None = Field(None, description="當天開館時間 HH:MM，休館為 None")
    close: str | None = Field(None, description="當天閉館時間 HH:MM，休館為 None")
    note: str | None = Field(None, description="例：國慶日、臨時休館")


# ---------- 送件 forward_reservation() ----------
class ForwardReceipt(BaseModel):
    """把預約送到中心後的回執。"""

    accepted: bool = Field(..., description="中心是否已收到")
    center_reference: str | None = Field(None, description="中心那邊的單號（如果有）")
    message: str | None = Field(None, description="失敗原因，不要放個資")
