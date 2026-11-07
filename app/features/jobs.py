"""背景排程：在 main.py 的 lifespan 啟動。

- 庫存同步：每 30–60 秒呼叫爬蟲 fetch_stock
- 逾期掃描：每分鐘自動取消逾期借用、送取貨提醒、清過期事件
- 送件佇列：定期送出待送的預約
- 推播檢查：每 PUSH_CHECK_MINUTES 分鐘檢查官網新公告（→ 推播 service.notice）、重試失敗的推播
  （到貨通知是在庫存同步時判斷 0 → >0 推播；取貨提醒 / 逾期是每分鐘排程推播）
"""

import asyncio
from collections.abc import Awaitable, Callable

from app.config import get_settings
from app.features.forwarding import service as forwarding_service
from app.features.mailbox import service as mailbox_service
from app.features.notification import notice_watch
from app.features.notification import service as notification_service
from app.features.reservation import service as reservation_service
from app.features.stock import service as stock_service
from app.tools.logger import get_logger

logger = get_logger(__name__)


async def _loop(name: str, seconds: int, fn: Callable[[], Awaitable[object]]) -> None:
    warned_not_impl = False
    while True:
        try:
            await fn()
        except NotImplementedError as exc:
            if not warned_not_impl:
                logger.warning("[%s] 爬蟲尚未實作：%s", name, exc)
                warned_not_impl = True
        except Exception as exc:  # noqa: BLE001
            logger.error("[%s] failed: %s", name, type(exc).__name__)
        await asyncio.sleep(seconds)


async def _minutely() -> None:
    await reservation_service.expire_overdue()
    await reservation_service.send_pickup_reminders()
    mailbox_service.purge_expired()


async def _push_check() -> None:
    try:
        await notice_watch.check_new_notices()
    finally:
        # 公告爬蟲還沒寫好（NotImplementedError）也照樣重試失敗的推播
        await notification_service.retry_failed()


def start() -> list[asyncio.Task]:
    s = get_settings()
    return [
        asyncio.create_task(_loop("stock-sync", s.stock_sync_seconds, stock_service.sync_from_source)),
        asyncio.create_task(_loop("minutely", s.expire_scan_seconds, _minutely)),
        asyncio.create_task(_loop("forward", s.forward_retry_seconds, forwarding_service.process_due)),
        asyncio.create_task(_loop("push-check", s.push_check_minutes * 60, _push_check)),
    ]


async def stop(tasks: list[asyncio.Task]) -> None:
    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
