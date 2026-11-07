"""到貨通知訂閱（記憶體版）。插入順序 = 候補順序。"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class SubscriptionRow:
    id: str
    mailbox_id: str
    variant_id: str
    category_id: str | None
    created_at: datetime


subscriptions: dict[str, SubscriptionRow] = {}


def reset() -> None:
    subscriptions.clear()
