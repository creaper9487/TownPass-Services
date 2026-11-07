"""POST /reservations 欄位。

欄位規則（必填、長度、格式、選項）全部來自 app/config.py 的 FIELDS；
服務要填哪些欄位、items 可以選什麼來自 config.SERVICES。這裡不寫死規則。

contact / subject / pickup / other_text 是個資：不存資料庫、不進日誌。
"""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.tools.fields import field, field_type

CenterId = Literal["heyi", "south", "west"]
Status = Literal["booked", "submitted", "confirmed", "completed", "cancelled", "expired"]


class Contact(BaseModel):
    name: field_type("contact.name") = field("contact.name")
    mobile: field_type("contact.mobile") = field("contact.mobile")
    phone: field_type("contact.phone") = field("contact.phone")
    gender: field_type("contact.gender") = field("contact.gender")
    email: field_type("contact.email") = field("contact.email")


class Subject(BaseModel):
    """輔具使用者（評估、維修）。"""

    name: field_type("subject.name") = field("subject.name")
    id_no: field_type("subject.id_no") = field("subject.id_no")
    registered_district: field_type("subject.registered_district") = field("subject.registered_district")
    living_county: field_type("subject.living_county") = field("subject.living_county")
    living_district: field_type("subject.living_district") = field("subject.living_district")
    remark: field_type("subject.remark") = field("subject.remark")


class Pickup(BaseModel):
    """回收地點。"""

    district: field_type("pickup.district") = field("pickup.district")
    address: field_type("pickup.address") = field("pickup.address")
    has_elevator: field_type("pickup.has_elevator") = field("pickup.has_elevator")
    need_certificate: field_type("pickup.need_certificate") = field("pickup.need_certificate")
    remark: field_type("pickup.remark") = field("pickup.remark")


class ReservationCreate(BaseModel):
    """哪些欄位必填、items 能選什麼，由 service 層依 config.SERVICES 檢查（validate_against_config）。"""

    service: str = Field(..., description="borrow / assess / repair / recycle（config.SERVICES 開著的）")
    mailbox_id: str
    center_id: CenterId | None = None  # borrow 必填；其他由後端依行政區決定
    items: list[str] = Field(..., min_length=1)
    other_text: field_type("other_text") = field("other_text")
    contact: Contact
    subject: Subject | None = None
    pickup: Pickup | None = None


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


class FormOut(BaseModel):
    """GET /forms/{service}"""

    service: str
    label: str
    item_options: list[str]
    allow_other: bool
    max_items: int
    required_fields: list[str]
    districts: list[str]
    fields: dict[str, dict]
