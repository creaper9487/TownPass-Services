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
    variant_name, category_name = await catalog_service.variant_names(payload.variant_id)
    sub_id = new_id("sub")
    repo.insert(repo.SubscriptionRow(sub_id, payload.mailbox_id, payload.variant_id, category_id, now(),
                                     variant_name=variant_name, category_name=category_name))
    return sub_id


def list_for(mailbox_id: str) -> list[SubscriptionOut]:
    return [SubscriptionOut(id=s.id, variant_id=s.variant_id, variant_name=s.variant_name,
                            category_id=s.category_id, category_name=s.category_name, status=s.status,
                            created_at=s.created_at, arrived_at=s.arrived_at) for s in repo.by_mailbox(mailbox_id)]


def get(sub_id: str) -> repo.SubscriptionRow:
    row = repo.get(sub_id)
    if row is None:
        raise E.not_found("訂閱")
    return row


def delete(sub_id: str) -> None:
    repo.delete(sub_id)


async def _notify(sub: repo.SubscriptionRow) -> None:
    """寫進「這個人」的信箱 → 推播給這個信箱登記的裝置（不是廣播）。

    data 帶品項名稱（variant_name / category_name），App 收到後可以顯示「什麼到貨了」。
    名稱只放 data，不放通知標題 / 內容（鎖定畫面看得到，見 notification/texts.py）。
    舊訂閱沒存名稱時，這時再查一次目錄。
    """
    variant_name, category_name = sub.variant_name, sub.category_name
    if variant_name is None:
        variant_name, category_name = await catalog_service.variant_names(sub.variant_id)
    mailbox_service.append_event(sub.mailbox_id, "stock.arrived",
                                 ref={"variant_id": sub.variant_id, "subscription_id": sub.id},
                                 data={"variant_name": variant_name, "category_name": category_name})


async def force_arrive(variant_id: str | None = None, mailbox_id: str | None = None) -> list[repo.SubscriptionRow]:
    """手動：把等待中的訂閱直接改成已到貨並推播（不管官網有沒有貨）。不給條件 = 全部。"""
    done = []
    for sub in repo.waiting(variant_id, mailbox_id):
        if repo.mark_arrived(sub.id, now()):
            await _notify(sub)
            done.append(sub)
    if done:
        logger.info("force arrived: %d subscription(s)", len(done))
    return done


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
            await _notify(sub)
    if count:
        logger.info("stock.arrived: %d subscription(s) notified", count)
    return count
