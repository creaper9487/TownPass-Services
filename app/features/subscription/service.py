"""到貨通知。

- 同信箱同類別「等待中」最多 1 筆（官方規則：同類型輔具只可候補一件）。
- 品項必須存在、而且是 config 開放借用的（catalog_service.check_variant）。
- 每次庫存更新後（背景排程每 3 分鐘、中心 webhook、取消釋回）都跑 check_arrivals()：
  等待中、而且品項現在有貨的訂閱 → SQL 狀態改成 arrived（已到貨）→ 只推給「這個訂閱人」的裝置。
  每個品項一次最多通知「目前庫存數」位，依候補順序。
"""

from app.features.catalog import service as catalog_service
from app.features.mailbox import service as mailbox_service
from app.features.subscription import repository as repo
from app.features.subscription.schemas import SubscriptionCreate, SubscriptionOut
from app.tools import exceptions as E
from app.tools.logger import get_logger
from app.tools.security import new_id
from app.tools.timeutil import now

logger = get_logger(__name__)


async def create(payload: SubscriptionCreate) -> str:
    category_id = await catalog_service.check_variant(payload.variant_id, field="variant_id")
    for s in repo.by_mailbox(payload.mailbox_id, status="waiting"):
        if (category_id and s.category_id == category_id) or s.variant_id == payload.variant_id:
            raise E.duplicate_waitlist()
    sub_id = new_id("sub")
    repo.insert(repo.SubscriptionRow(sub_id, payload.mailbox_id, payload.variant_id, category_id, now()))
    return sub_id


def list_for(mailbox_id: str) -> list[SubscriptionOut]:
    return [SubscriptionOut(id=s.id, variant_id=s.variant_id, category_id=s.category_id, status=s.status,
                            created_at=s.created_at, arrived_at=s.arrived_at) for s in repo.by_mailbox(mailbox_id)]


def get(sub_id: str) -> repo.SubscriptionRow:
    row = repo.get(sub_id)
    if row is None:
        raise E.not_found("訂閱")
    return row


def delete(sub_id: str) -> None:
    repo.delete(sub_id)


async def check_arrivals() -> int:
    """等待中、而且現在有貨的訂閱 → arrived + 推播給訂閱人。回傳這次通知了幾筆。"""
    notified: dict[str, int] = {}
    count = 0
    for sub, stock in repo.waiting_with_stock():
        if notified.get(sub.variant_id, 0) >= stock:
            continue
        if repo.mark_arrived(sub.id, now()):
            notified[sub.variant_id] = notified.get(sub.variant_id, 0) + 1
            count += 1
            # 寫進「這個人」的信箱 → 推播給這個信箱登記的裝置（不是廣播）
            mailbox_service.append_event(sub.mailbox_id, "stock.arrived",
                                         ref={"variant_id": sub.variant_id, "subscription_id": sub.id})
    if count:
        logger.info("stock.arrived: %d subscription(s) notified", count)
    return count
