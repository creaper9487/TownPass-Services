"""庫存：背景從爬蟲同步、借用時扣庫存、取消時釋回、庫存 0 → >0 時通知訂閱者。"""

from app.features.stock import repository as repo
from app.tools import exceptions as E
from app.tools.crawlers import fetch_stock
from app.tools.crawlers.runner import run_crawler
from app.tools.crawlers.schemas import StockItem
from app.tools.logger import get_logger

logger = get_logger(__name__)


def snapshot(since: int | None = None) -> dict:
    """GET /stock 的內容。since 有給就只回比 since 新的品項。"""
    items = {
        r.variant_id: {"stock": r.stock, "waiting": r.waiting}
        for r in repo.rows.values()
        if since is None or r.version > since
    }
    return {"version": repo.current_version(), "as_of": repo.as_of().isoformat(), "items": items}


def get(variant_id: str) -> repo.StockRow | None:
    return repo.rows.get(variant_id)


async def apply_items(items: list[StockItem]) -> list[str]:
    """套用一批庫存（來自爬蟲或中心 webhook），回傳有變動的 variant_id。"""
    from app.features.subscription import service as subscription_service

    changed: list[str] = []
    arrived: list[tuple[str, int]] = []
    for item in items:
        row = repo.rows.get(item.variant_id)
        if row and row.stock == item.stock and row.waiting == item.waiting:
            continue
        before = row.stock if row else 0
        version = repo.bump_version()
        repo.rows[item.variant_id] = repo.StockRow(item.variant_id, item.stock, item.waiting, version)
        changed.append(item.variant_id)
        if before == 0 and item.stock > 0:
            arrived.append((item.variant_id, item.stock))

    for variant_id, count in arrived:
        await subscription_service.on_arrival(variant_id, count)
    return changed


async def sync_from_source() -> int:
    """背景工作：呼叫爬蟲取得全部庫存並套用。"""
    items = await run_crawler(fetch_stock, list[StockItem])
    changed = await apply_items(items)
    return len(changed)


def reserve(variant_ids: list[str]) -> None:
    """借用：全部有庫存才一起扣（同一個交易，任何一個不夠就都不扣）。"""
    for vid in variant_ids:
        row = repo.rows.get(vid)
        if row is None or row.stock <= 0:
            raise E.out_of_stock(row.stock if row else 0, row.waiting if row else 0)
    for vid in variant_ids:
        row = repo.rows[vid]
        row.stock -= 1
        row.version = repo.bump_version()


async def release(variant_ids: list[str]) -> None:
    """取消 / 逾期：釋回庫存；0 → 1 時一樣會通知訂閱者。"""
    from app.features.subscription import service as subscription_service

    for vid in variant_ids:
        row = repo.rows.get(vid)
        if row:
            row.stock += 1
            row.version = repo.bump_version()
            if row.stock == 1:
                await subscription_service.on_arrival(vid, 1)
