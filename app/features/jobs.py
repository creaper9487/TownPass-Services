"""背景排程：在 main.py 的 lifespan 啟動。

- 庫存同步：每 30–60 秒呼叫爬蟲 fetch_stock
- 逾期掃描：每分鐘自動取消逾期借用、送取貨提醒、清過期事件
- 送件佇列：定期送出待送的預約
- 推播檢查：每 PUSH_CHECK_MINUTES 分鐘檢查官網新公告（→ 推播 service.notice）、重試失敗的推播
  （到貨通知是在庫存同步時判斷 0 → >0 推播；取貨提醒 / 逾期是每分鐘排程推播）
"""

import asyncio
from collections.abc import Awaitable, Callable

from app import config
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


async def sync_now() -> dict:
    """立刻跑一次「抓資料 → 有變化就推播」（測試面板 / CLI 用，背景排程也是做同一件事）。"""
    from app.tools import db

    before = db.query("SELECT COALESCE(MAX(id), 0) AS m FROM push_log")[0]["m"]
    before_ev = db.query("SELECT COALESCE(MAX(rowid), 0) AS m FROM events")[0]["m"]
    result: dict = {"stock_changed": 0, "new_notices": 0, "errors": []}
    for step, fn in (("notices", notice_watch.check_new_notices), ("stock", stock_service.sync_from_source),
                     ("notices", notice_watch.check_new_notices)):
        try:
            n = await fn()
            result["stock_changed" if step == "stock" else "new_notices"] += n
        except NotImplementedError as exc:
            if f"{step}:" not in " ".join(result["errors"]):
                result["errors"].append(f"{step}: {exc}")
        except Exception as exc:  # noqa: BLE001  官網連不到、格式變了…：記下來，其他步驟照跑
            reason = getattr(exc, "code", type(exc).__name__)  # SOURCE_UNAVAILABLE = 官網抓不到
            logger.error("[sync] %s failed: %s", step, reason)
            result["errors"].append(f"{step}: {reason}")
    await notification_service.drain()
    pushes = db.query("SELECT type, result FROM push_log WHERE id > ? ORDER BY id", (before,))
    result["pushes"] = [dict(p) for p in pushes]
    # 寫進信箱的事件（推播是推給「該信箱登記的裝置」；沒裝置就只會在信箱裡，要靠 App / 網頁 pull）
    events = db.query(
        "SELECT e.type, e.mailbox_id, (SELECT COUNT(*) FROM devices d WHERE d.mailbox_id = e.mailbox_id) AS devices "
        "FROM events e WHERE e.rowid > ? ORDER BY e.rowid", (before_ev,))
    result["events"] = [dict(e) for e in events]
    return result


def start() -> list[asyncio.Task]:
    return [
        asyncio.create_task(_loop("stock-sync", config.STOCK_SYNC_SECONDS, stock_service.sync_from_source)),
        asyncio.create_task(_loop("minutely", config.EXPIRE_SCAN_SECONDS, _minutely)),
        asyncio.create_task(_loop("forward", config.FORWARD_RETRY_SECONDS, forwarding_service.process_due)),
        asyncio.create_task(_loop("push-check", config.PUSH_CHECK_MINUTES * 60, _push_check)),
    ]


async def stop(tasks: list[asyncio.Task]) -> None:
    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
