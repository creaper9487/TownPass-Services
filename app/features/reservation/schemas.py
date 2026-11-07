"""POST /reservations 欄位（規格「POST /reservations 欄位」表）。

contact / subject / pickup / other_text 是個資：只轉送，不存資料庫、不進日誌。
本系統只服務臺北市：居住縣市不是臺北市、或行政區不在臺北市 12 區 → 422 NOT_ELIGIBLE。
"""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

Service = Literal["borrow", "assess", "repair", "recycle"]
CenterId = Literal["heyi", "south", "west"]
Status = Literal["booked", "submitted", "confirmed", "completed", "cancelled", "expired"]


class Contact(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    mobile: str = Field(..., pattern=r"^09\d{8}$")
    phone: str | None = Field(None, max_length=20)
    gender: Literal["M", "F", "X"]
    email: str | None = Field(None, max_length=100)


class Subject(BaseModel):
    """輔具使用者（評估、維修）。"""

    name: str = Field(..., min_length=1, max_length=50)
    id_no: str = Field(..., pattern=r"^[A-Z][0-9A-Z]\d{8}$")
    registered_district: str  # 戶籍行政區
    living_county: str  # 居住縣市，只收「臺北市」
    living_district: str  # 居住行政區（決定由哪間中心服務）
    remark: str | None = Field(None, max_length=500)


class Pickup(BaseModel):
    """回收地點。"""

    district: str  # 回收地點行政區（臺北市），決定由哪間中心收取
    address: str = Field(..., min_length=1, max_length=200)
    has_elevator: bool
    need_certificate: bool
    remark: str | None = Field(None, max_length=500)


class ReservationCreate(BaseModel):
    service: Service
    mailbox_id: str
    center_id: CenterId | None = None  # borrow 必填；其他由後端依行政區決定
    items: list[str] = Field(..., min_length=1)
    other_text: str | None = Field(None, max_length=500)
    contact: Contact
    subject: Subject | None = None
    pickup: Pickup | None = None

    @model_validator(mode="after")
    def _check_by_service(self):
        if self.service == "borrow" and self.center_id is None:
            raise ValueError("center_id")
        if self.service in ("assess", "repair") and self.subject is None:
            raise ValueError("subject")
        if self.service == "recycle" and self.pickup is None:
            raise ValueError("pickup")
        return self


class PickupInfo(BaseModel):
    deadline: date
    open_dates: list[date]


class ReservationCreated(BaseModel):
    """POST /reservations 回傳。access_key 只回這一次，前端自己保存。"""

    id: str
    access_key: str
    status: Status
    pickup: PickupInfo | None = None


class ReservationStatus(BaseModel):
    """POST /reservations:batchGet 每一筆（不含任何個資）。"""

    id: str
    status: Status
    version: int
    updated_at: datetime
    pickup: PickupInfo | None = None


class BatchGetError(BaseModel):
    id: str
    error: Literal["BAD_KEY"] = "BAD_KEY"


class CancelResult(BaseModel):
    id: str
    status: Status
    version: int


class AccessKeyIn(BaseModel):
    access_key: str


class BatchGetItem(BaseModel):
    id: str
    access_key: str
