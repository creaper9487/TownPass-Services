"""服務中心與開館行事曆。"""

from datetime import date, timedelta

from app import config
from app.tools import exceptions as E
from app.tools.cache import TTLCache, etag_of
from app.tools.crawlers import fetch_center_calendar, fetch_centers
from app.tools.crawlers.runner import run_crawler
from app.tools.crawlers.schemas import CalendarDay, Center
from app.tools.districts import CENTER_IDS

_centers_cache = TTLCache(ttl_seconds=3600)
_calendar_cache = TTLCache(ttl_seconds=300)



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
    """借用取貨期限：回傳 (期限日, 可以取貨的日子)。

    config.CHECK_OPENING_HOURS = False：不管開館，期限內每一天都可以取貨。
    config.CHECK_OPENING_HOURS = True ：只算開館日，沒有開館日 → PICKUP_WINDOW_CLOSED。
    """
    days = config.PICKUP_DAYS
    deadline = today + timedelta(days=days - 1)
    if not config.CHECK_OPENING_HOURS:
        return deadline, [today + timedelta(days=i) for i in range(days)]
    calendar = await get_calendar(center_id, today, days)
    open_dates = [d.date for d in calendar if d.open]
    if not open_dates:
        raise E.pickup_window_closed()
    return deadline, open_dates
