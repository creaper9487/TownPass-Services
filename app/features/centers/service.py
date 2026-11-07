"""服務中心與開館行事曆。"""

from datetime import date, timedelta

from app.tools import exceptions as E
from app.tools.cache import TTLCache, etag_of
from app.tools.crawlers import fetch_center_calendar, fetch_centers
from app.tools.crawlers.runner import run_crawler
from app.tools.crawlers.schemas import CalendarDay, Center
from app.tools.districts import CENTER_IDS

_centers_cache = TTLCache(ttl_seconds=3600)
_calendar_cache = TTLCache(ttl_seconds=300)

PICKUP_DAYS = 2  # 規格：預約後 2 天內（含當日）取貨


async def get_centers() -> tuple[list[dict], str]:
    cached = _centers_cache.get()
    if cached is None:
        centers = await run_crawler(fetch_centers, list[Center])
        data = [c.model_dump(mode="json", by_alias=True) for c in centers]
        cached = (data, etag_of(data))
        _centers_cache.set(cached)
    return cached


async def get_calendar(center_id: str, start: date, days: int) -> list[CalendarDay]:
    if center_id not in CENTER_IDS:
        raise E.not_found("中心")
    key = (center_id, start, days)
    cached = _calendar_cache.get(key)
    if cached is None:
        cached = await run_crawler(fetch_center_calendar, list[CalendarDay], center_id, start, days)
        _calendar_cache.set(cached, key)
    return cached


async def pickup_window(center_id: str, today: date) -> tuple[date, list[date]]:
    """借用取貨期限：回傳 (期限日, 期限內的開館日)。沒有開館日 → PICKUP_WINDOW_CLOSED。"""
    calendar = await get_calendar(center_id, today, PICKUP_DAYS)
    open_dates = [d.date for d in calendar if d.open]
    if not open_dates:
        raise E.pickup_window_closed()
    return today + timedelta(days=PICKUP_DAYS - 1), open_dates
