"""檢查官網公告；發現新公告 id 就推播 service.notice。

- 已看過的公告 id 存在 SQLite（notice_seen），server 重啟、CLI 執行都不會重複推。
- 第一次檢查（DB 裡還沒有任何紀錄）只記住目前有哪些公告，不推播（避免把舊公告全部推一次）。
- 已結束（ends_at 已過）的公告不推。
"""

from app.features.mailbox import service as mailbox_service
from app.tools import db
from app.tools.crawlers import fetch_notices
from app.tools.crawlers.runner import run_crawler
from app.tools.crawlers.schemas import Notice
from app.tools.logger import get_logger
from app.tools.timeutil import now

logger = get_logger(__name__)

latest: list[Notice] = []  # 最近一次抓到的有效公告（之後給 GET /notices 用）


def _remember(ids: list[str]) -> None:
    ts = now().isoformat()
    for i in ids:
        db.execute("INSERT OR IGNORE INTO notice_seen(id, created_at) VALUES (?, ?)", (i, ts))


async def check_new_notices() -> int:
    """回傳這次推播了幾則新公告。爬蟲還沒寫好會 raise NotImplementedError。"""
    global latest
    notices = await run_crawler(fetch_notices, list[Notice])
    t = now()
    active = [n for n in notices if n.ends_at is None or n.ends_at > t]
    latest = active
    if db.get_meta("notice_seeded") is None:
        _remember([n.id for n in notices])
        db.set_meta("notice_seeded", t.isoformat())
        return 0
    seen = {r["id"] for r in db.query("SELECT id FROM notice_seen")}
    new = [n for n in active if n.id not in seen]
    _remember([n.id for n in notices])
    for n in sorted(new, key=lambda n: n.published_at):
        mailbox_service.broadcast("service.notice", {"notice_id": n.id, "title": n.title,
                                                     "center_ids": list(n.center_ids)})
    if new:
        logger.info("pushed %d new notice(s)", len(new))
    return len(new)


def reset() -> None:
    global latest
    db.execute("DELETE FROM notice_seen")
    db.execute("DELETE FROM meta WHERE key = 'notice_seeded'")
    latest = []
