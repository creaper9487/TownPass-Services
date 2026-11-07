from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

EventType = Literal[
    "reservation.booked",
    "reservation.pickup_reminder",
    "reservation.expired",
    "reservation.confirmed",
    "reservation.completed",
    "reservation.cancelled",
    "stock.arrived",
    "service.notice",
]


class MailboxCreated(BaseModel):
    mailbox_id: str
    mailbox_key: str  # 只在建立時回傳一次


class Event(BaseModel):
    cursor: int
    id: str
    type: EventType
    ts: datetime
    ref: dict[str, Any] = {}
    data: dict[str, Any] = {}
    expires_at: datetime


class EventsPage(BaseModel):
    events: list[Event]
    next_cursor: int  # 下次請帶這個 cursor


class AckIn(BaseModel):
    cursor: int
