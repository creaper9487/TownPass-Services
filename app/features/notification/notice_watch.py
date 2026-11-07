"""每 N 分鐘檢查官網公告；發現新公告 id 就推播 service.notice。

- 第一次檢查只記住目前有哪些公告，不推播（避免後端一啟動就把舊公告全部推一次）。
- 已結束（ends_at 已過）的公告不推。
"""

from app.features.mailbox import service as mailbox_service
from app.tools.crawlers import fetch_notices
from app.tools.crawlers.runner import run_crawler
from app.tools.crawlers.schemas import Notice
from app.tools.logger import get_logger
from app.tools.timeutil import now

logger = get_logger(__name__)

_seen: set[str] = set()
_seeded = False
latest: list[Notice] = []  # 最近一次抓到的有效公告（之後給 GET /notices 用）


async def check_new_notices() -> int:
    """回傳這次推播了幾則新公告。爬蟲還沒寫好會 raise NotImplementedError。"""
    global _seeded, latest
    notices = await run_crawler(fetch_notices, list[Notice])
    t = now()
    active = [n for n in notices if n.ends_at is None or n.ends_at > t]
    latest = active
    if not _seeded:
        _seen.update(n.id for n in notices)
        _seeded = True
        return 0
    new = [n for n in active if n.id not in _seen]
    _seen.update(n.id for n in notices)
    for n in sorted(new, key=lambda n: n.published_at):
        mailbox_service.broadcast("service.notice", {"notice_id": n.id, "title": n.title,
                                                     "center_ids": list(n.center_ids)})
    if new:
        logger.info("pushed %d new notice(s)", len(new))
    return len(new)


def reset() -> None:
    global _seeded, latest
    _seen.clear()
    _seeded = False
    latest = []
