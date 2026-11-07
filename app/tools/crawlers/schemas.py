"""爬蟲回傳格式（契約）。欄位名稱直接等於 API 回給前端的格式，爬蟲組照這裡填就好。

ID 規則：
- 類別 id / 款式 id：用官網上的原始代碼（option value、網址參數…）轉成字串；
  一定要「穩定」，同一個東西每次爬都要得到同一個 id，庫存、到貨通知都靠它對應。
- 中心 id：固定為 "heyi"（合宜）/ "south"（南區）/ "west"（西區）。
- 時間一律 24 小時制 "HH:MM"。
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CenterId = Literal["heyi", "south", "west"]
HHMM = r"^\d{2}:\d{2}$"


class TimeRange(BaseModel):
    """一段開館時間，例：{"from": "08:30", "to": "12:00"}"""

    model_config = ConfigDict(populate_by_name=True)

    from_: str = Field(..., alias="from", pattern=HHMM, description="開始 HH:MM")
    to: str = Field(..., pattern=HHMM, description="結束 HH:MM")


# ---------- 目錄 fetch_catalog() → GET /catalog ----------
class VariantAttrs(BaseModel):
    """可篩選的數值屬性（官網規格裡有寫才填，沒有就 None）。"""

    height_min: float | None = Field(None, description="適用身高下限（公分）")
    height_max: float | None = Field(None, description="適用身高上限（公分）")
    seat_width_in: float | None = Field(None, description="座寬（英吋）")
    weight_max_kg: float | None = Field(None, description="最大承重（公斤）")


class CatalogVariant(BaseModel):
    """一款輔具，例：一般型輪椅。官網共約 62 款。"""

    id: str = Field(..., description="款式代碼（= 庫存的 variant_id），穩定不變")
    name: str = Field(..., description="款式名稱")
    image: str | None = Field(None, description="照片完整網址")
    specs: list[str] = Field(default_factory=list, description="規格，一行一筆，例：['座寬 18 吋', '重量 15 公斤']")
    description: str | None = Field(None, description="說明 / 注意事項")
    attrs: VariantAttrs | None = None


class CatalogCategory(BaseModel):
    """一個分類，例：輪椅類。官網共約 12 類。"""

    id: str = Field(..., description="類別代碼，穩定不變")
    name: str = Field(..., description="類別名稱")
    image: str | None = Field(None, description="類別代表圖完整網址")
    variants: list[CatalogVariant] = Field(default_factory=list)


# ---------- 庫存 fetch_stock() → GET /stock ----------
class StockItem(BaseModel):
    variant_id: str = Field(..., description="= CatalogVariant.id")
    stock: int = Field(..., ge=0, description="剩餘數量")
    waiting: int = Field(..., ge=0, description="等待人數")


# ---------- 中心 fetch_centers() → GET /centers ----------
class Center(BaseModel):
    id: CenterId
    name: str = Field(..., description="例：臺北市合宜輔具中心")
    address: str
    phone: str
    districts: list[str] = Field(..., description="負責的臺北市行政區")
    open_days: list[int] = Field(..., description="每週開館日，1=星期一 … 7=星期日，例：[1,2,3,4,5]")
    hours: list[TimeRange] = Field(..., description="開館時段，有午休就兩段")
    lat: float = Field(..., description="緯度（約略即可）")
    lng: float = Field(..., description="經度")


# ---------- 行事曆 fetch_center_calendar() → GET /centers/{id}/calendar ----------
class CalendarDay(BaseModel):
    date: date
    open: bool = Field(..., description="這天有沒有開館")
    hours: list[TimeRange] = Field(default_factory=list, description="這天的開館時段；休館為 []")
    reason: str | None = Field(None, description="休館原因，例：國慶日、臨時休館；開館日為 None")


# ---------- 送件 forward_reservation() ----------
class ForwardReceipt(BaseModel):
    accepted: bool = Field(..., description="中心是否已收到")
    center_reference: str | None = Field(None, description="中心那邊的單號（如果有）")
    message: str | None = Field(None, description="失敗原因，不要放個資")
