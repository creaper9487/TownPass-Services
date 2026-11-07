"""到貨通知：同信箱同類別最多 1 筆（官方規則：同類型輔具只可候補一件）。

到貨分配（預設做法，待中心確認）：依訂閱順序通知前 k 位（k = 到貨數），不保留優先期。
品項必須存在、而且是 config 開放借用的（catalog_service.check_variant）。
"""

from app.features.catalog import service as catalog_service
from app.features.mailbox import service as mailbox_service
from app.features.subscription import repository as repo
from app.features.subscription.schemas import SubscriptionCreate
from app.tools import exceptions as E
from app.tools.security import new_id
from app.tools.timeutil import now


async def create(payload: SubscriptionCreate) -> str:
    category_id = await catalog_service.check_variant(payload.variant_id, field="variant_id")
    for s in repo.by_mailbox(payload.mailbox_id):
        if (category_id and s.category_id == category_id) or s.variant_id == payload.variant_id:
            raise E.duplicate_waitlist()
    sub_id = new_id("sub")
    repo.insert(repo.SubscriptionRow(sub_id, payload.mailbox_id, payload.variant_id, category_id, now()))
    return sub_id


def get(sub_id: str) -> repo.SubscriptionRow:
    row = repo.get(sub_id)
    if row is None:
        raise E.not_found("訂閱")
    return row


def delete(sub_id: str) -> None:
    repo.delete(sub_id)


async def on_arrival(variant_id: str, count: int) -> None:
    """庫存 0 → >0：通知前 count 位訂閱者，通知後刪除訂閱。"""
    for s in repo.waiting_for(variant_id, count):
        mailbox_service.append_event(s.mailbox_id, "stock.arrived", ref={"variant_id": variant_id})
        repo.delete(s.id)
