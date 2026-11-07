"""品項目錄：從爬蟲取得，快取 1 小時；依 config 過濾開放借用的分類 / 品項。

官網連不到時，改用「上一次成功抓到的目錄」（存在 SQLite，server 重啟也還在）；連一次都沒抓到過才回 503。
"""

import json

from app import config
from app.tools import db
from app.tools import exceptions as E
from app.tools.cache import TTLCache, etag_of
from app.tools.crawlers import fetch_catalog
from app.tools.crawlers.runner import run_crawler
from app.tools.crawlers.schemas import CatalogCategory
from app.tools.logger import get_logger

logger = get_logger(__name__)

_cache = TTLCache(ttl_seconds=3600)


def _filter(data: list[dict]) -> list[dict]:
    """套用 config.BORROW_CATEGORIES、config.BLOCKED_VARIANTS。"""
    cats, blocked = config.BORROW_CATEGORIES, set(config.BLOCKED_VARIANTS)
    out = []
    for c in data:
        if cats is not None and c["id"] not in cats:
            continue
        variants = [v for v in c["variants"] if v["id"] not in blocked]
        if variants:
            out.append({**c, "variants": variants})
    return out


async def get_catalog() -> tuple[list[dict], str]:
    """回傳 (開放借用的分類列表, ETag)。"""
    cached = _cache.get()
    if cached is None:
        try:
            categories = await run_crawler(fetch_catalog, list[CatalogCategory])
            cached = [c.model_dump() for c in categories]
            db.set_meta("catalog_last_good", json.dumps(cached, ensure_ascii=False))
            _cache.set(cached)
        except E.AppError:
            last = db.get_meta("catalog_last_good")
            if last is None:
                raise
            logger.warning("catalog source unavailable, serving last good copy")
            cached = json.loads(last)  # 不放進快取：下一個請求會再試官網
    data = _filter(cached)
    return data, etag_of(data)


async def category_of(variant_id: str) -> str | None:
    """查某款式屬於哪個分類；目錄還拿不到或找不到時回 None。"""
    try:
        data, _ = await get_catalog()
    except NotImplementedError:
        return None
    for cat in data:
        if any(v["id"] == variant_id for v in cat["variants"]):
            return cat["id"]
    return None


async def check_variant(variant_id: str, field: str = "variant_id") -> str | None:
    """品項必須存在且開放借用（config），否則 422 INVALID_FIELD。回傳分類 id。

    目錄抓不到時（爬蟲壞掉 / 還沒寫）退而查庫存表：庫存裡有這個品項就當存在，分類未知回 None。
    """
    if variant_id in config.BLOCKED_VARIANTS:
        raise E.invalid_field([field])
    try:
        data, _ = await get_catalog()
    except Exception as exc:  # noqa: BLE001
        from app.features.stock import repository as stock_repo

        logger.warning("catalog unavailable (%s), checking stock table instead", type(exc).__name__)
        if stock_repo.get(variant_id) is None:
            raise E.invalid_field([field]) from None
        return None
    for cat in data:
        if any(v["id"] == variant_id for v in cat["variants"]):
            return cat["id"]
    raise E.invalid_field([field])  # 不存在，或分類沒開放（已被 _filter 過濾掉）
