from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class CenterStatusHook(BaseModel):
    event_id: str
    reservation_id: str
    status: Literal["confirmed", "completed", "cancelled"]
    occurred_at: datetime


class CenterStockHook(BaseModel):
    event_id: str
    variant_id: str
    stock: int = Field(..., ge=0)
    waiting: int = Field(..., ge=0)
