"""到貨通知：同信箱同類別最多 1 筆（官方規則：同類型輔具只可候補一件）。

到貨分配（預設做法，待中心確認）：依訂閱順序通知前 k 位（k = 到貨數），不保留優先期。
"""

from app.features.catalog import service as catalog_service
from app.features.mailbox import service as mailbox_service
from app.features.subscription import repository as repo
from app.features.subscription.schemas import SubscriptionCreate
from app.tools import exceptions as E
from app.tools.security import new_id
from app.tools.timeutil import now


async def create(payload: SubscriptionCreate) -> str:
    variant = await catalog_service.find_variant(payload.variant_id)
    # 目錄還抓不到時 category 未知，退而以 variant 判斷重複
    category_id = variant.category_id if variant else None
    for s in repo.subscriptions.values():
        if s.mailbox_id != payload.mailbox_id:
            continue
        same = (category_id and s.category_id == category_id) or s.variant_id == payload.variant_id
        if same:
            raise E.duplicate_waitlist()
    sub_id = new_id("sub")
    repo.subscriptions[sub_id] = repo.SubscriptionRow(
        sub_id, payload.mailbox_id, payload.variant_id, category_id, now()
    )
    return sub_id


def get(sub_id: str) -> repo.SubscriptionRow:
    row = repo.subscriptions.get(sub_id)
    if row is None:
        raise E.not_found("訂閱")
    return row


def delete(sub_id: str) -> None:
    repo.subscriptions.pop(sub_id, None)


async def on_arrival(variant_id: str, count: int) -> None:
    """庫存 0 → >0：通知前 count 位訂閱者，通知後刪除訂閱。"""
    waiting = [s for s in repo.subscriptions.values() if s.variant_id == variant_id][:count]
    for s in waiting:
        mailbox_service.append_event(s.mailbox_id, "stock.arrived", ref={"variant_id": variant_id})
        repo.subscriptions.pop(s.id, None)
