from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class SubscriptionCreate(BaseModel):
    mailbox_id: str
    variant_id: str


class SubscriptionCreated(BaseModel):
    id: str


class SubscriptionOut(BaseModel):
    """GET /subscriptions 每一筆。"""

    id: str
    variant_id: str
    variant_name: str | None = None  # 品項名稱（訂閱當下從目錄查到的）
    category_id: str | None
    category_name: str | None = None
    status: Literal["waiting", "arrived"]  # waiting = 等待中；arrived = 已到貨（已推播通知）
    created_at: datetime
    arrived_at: datetime | None
