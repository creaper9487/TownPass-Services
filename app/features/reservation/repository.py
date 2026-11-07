"""預約（記憶體版）。欄位對應規格「資料表 reservation」，全部不含個資。"""

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class ReservationRow:
    id: str
    access_key_hash: str
    mailbox_id: str
    service: str
    center_id: str
    items: list[str]
    status: str
    version: int
    pickup_deadline: date | None
    pickup_dates: list[date]
    forward_state: str  # pending / sent / failed
    created_at: datetime
    updated_at: datetime
    reminders_sent: set[str] = field(default_factory=set)


reservations: dict[str, ReservationRow] = {}
# Idempotency-Key → (request hash, reservation_id, access_key)
idempotency: dict[str, tuple[str, str, str]] = {}


def reset() -> None:
    reservations.clear()
    idempotency.clear()
