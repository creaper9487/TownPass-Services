"""庫存：背景從爬蟲同步、借用時扣庫存、取消時釋回、庫存 0 → >0 時通知訂閱者。"""

from app import config
from app.features.stock import repository as repo
from app.tools import db
from app.tools import exceptions as E
from app.tools.crawlers import fetch_stock
from app.tools.crawlers.runner import run_crawler
from app.tools.crawlers.schemas import StockItem
from app.tools.logger import get_logger

logger = get_logger(__name__)


def snapshot(since: int | None = None) -> dict:
    """GET /stock 的內容。since 有給就只回比 since 新的品項。config.BLOCKED_VARIANTS 不回傳。"""
    blocked = set(config.BLOCKED_VARIANTS)
    items = {r.variant_id: {"stock": r.stock, "waiting": r.waiting}
             for r in repo.all_rows(since) if r.variant_id not in blocked}
    return {"version": repo.current_version(), "as_of": repo.as_of().isoformat(), "items": items}


def get(variant_id: str) -> repo.StockRow | None:
    return repo.get(variant_id)


async def apply_items(items: list[StockItem]) -> list[str]:
    """套用一批庫存（來自爬蟲或中心 webhook），回傳有變動的 variant_id。"""
    from app.features.subscription import service as subscription_service

    changed: list[str] = []
    arrived: list[tuple[str, int]] = []
    for item in items:
        row = repo.get(item.variant_id)
        if row and row.stock == item.stock and row.waiting == item.waiting:
            continue
        before = row.stock if row else 0
        repo.put(item.variant_id, item.stock, item.waiting)
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
    with db.transaction() as c:
        rows = {}
        for vid in variant_ids:
            r = c.execute("SELECT * FROM stock WHERE variant_id = ?", (vid,)).fetchone()
            if r is None or r["stock"] <= 0:
                raise E.out_of_stock(r["stock"] if r else 0, r["waiting"] if r else 0)
            rows[vid] = r
        for vid, r in rows.items():
            repo.put(vid, r["stock"] - 1, r["waiting"], c)


async def release(variant_ids: list[str]) -> None:
    """取消 / 逾期：釋回庫存；0 → 1 時一樣會通知訂閱者。"""
    from app.features.subscription import service as subscription_service

    for vid in variant_ids:
        row = repo.get(vid)
        if row:
            repo.put(vid, row.stock + 1, row.waiting)
            if row.stock == 0:
                await subscription_service.on_arrival(vid, 1)
