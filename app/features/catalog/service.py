"""品項目錄：從爬蟲取得，快取 1 小時。"""

from app.tools.cache import TTLCache, etag_of
from app.tools.crawlers import fetch_catalog
from app.tools.crawlers.runner import run_crawler
from app.tools.crawlers.schemas import CatalogCategory

_cache = TTLCache(ttl_seconds=3600)


async def get_catalog() -> tuple[list[dict], str]:
    """回傳 (類別列表, ETag)。"""
    cached = _cache.get()
    if cached is None:
        categories = await run_crawler(fetch_catalog, list[CatalogCategory])
        data = [c.model_dump() for c in categories]
        cached = (data, etag_of(data))
        _cache.set(cached)
    return cached


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
