"""POST /reservations 欄位（規格「POST /reservations 欄位」表）。

contact / subject / pickup / other_text 是個資：只轉送，不存資料庫、不進日誌。
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
    registered_district: str
    living_county: str
    living_district: str
    remark: str | None = Field(None, max_length=500)


class Pickup(BaseModel):
    """回收地點。"""

    district: str
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


class ReservationOut(BaseModel):
    """預約狀態（不含任何個資）。"""

    id: str
    service: Service
    center_id: CenterId
    items: list[str]
    status: Status
    version: int
    pickup: PickupInfo | None = None
    created_at: datetime
    updated_at: datetime


class ReservationCreated(ReservationOut):
    access_key: str  # 只在建立時回傳一次，前端自己保存


class AccessKeyIn(BaseModel):
    access_key: str


class BatchGetItem(BaseModel):
    id: str
    access_key: str


class BatchGetIn(BaseModel):
    reservations: list[BatchGetItem] = Field(..., max_length=50)
