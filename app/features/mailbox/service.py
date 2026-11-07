"""匿名信箱：所有通知與預約狀態事件都寫進信箱，前端用 cursor pull。

- 寫入事件後，喚醒正在 long-poll / SSE 等待的連線，並推播（FCM）到該信箱登記的裝置。
- 事件保留 30 天；ack 之後可清除。
"""

import asyncio
from datetime import timedelta
from typing import Any

from app.features.mailbox import repository as repo
from app.features.mailbox.schemas import Event, EventType, MailboxCreated
from app.features.notification import service as notification_service
from app.tools import exceptions as E
from app.tools.security import hash_secret, new_id, new_secret, verify_secret
from app.tools.timeutil import now

EVENT_TTL = timedelta(days=30)
MAILBOX_IDLE_TTL = timedelta(days=180)

_waiters: dict[str, asyncio.Event] = {}


def _signal(mailbox_id: str) -> None:
    ev = _waiters.pop(mailbox_id, None)
    if ev:
        ev.set()


def create() -> MailboxCreated:
    key = new_secret()
    mailbox_id = new_id("mb")
    ts = now()
    repo.mailboxes[mailbox_id] = repo.MailboxRow(mailbox_id, hash_secret(key), ts, ts)
    return MailboxCreated(mailbox_id=mailbox_id, mailbox_key=key)


def exists(mailbox_id: str) -> bool:
    return mailbox_id in repo.mailboxes


def authenticate(mailbox_id: str, key: str | None) -> repo.MailboxRow:
    row = repo.mailboxes.get(mailbox_id)
    if row is None or not key or not verify_secret(key, row.key_hash):
        raise E.bad_key()
    row.last_seen_at = now()
    return row


def append_event(mailbox_id: str, type: EventType, ref: dict[str, Any] | None = None,
                 data: dict[str, Any] | None = None, push: bool = True) -> Event | None:
    row = repo.mailboxes.get(mailbox_id)
    if row is None:
        return None
    ts = now()
    event = Event(cursor=row.next_cursor, id=new_id("ev"), type=type, ts=ts,
                  ref=ref or {}, data=data or {}, expires_at=ts + EVENT_TTL)
    row.next_cursor += 1
    row.events.append(event)
    _signal(mailbox_id)
    if push:
        notification_service.notify_event(mailbox_id, event)
    return event


def broadcast(type: EventType, data: dict[str, Any]) -> int:
    """service.notice：公告寫進所有信箱（給 pull 補拉），推播只發一次 FCM topic。"""
    count = sum(1 for mid in list(repo.mailboxes) if append_event(mid, type, data=data, push=False))
    ts = now()
    notification_service.notify_topic(Event(cursor=0, id=new_id("ev"), type=type, ts=ts, data=data,
                                            expires_at=ts + EVENT_TTL))
    return count


def events_after(row: repo.MailboxRow, cursor: int) -> list[Event]:
    t = now()
    return [e for e in row.events if e.cursor > cursor and e.expires_at > t]


async def wait_events(row: repo.MailboxRow, cursor: int, wait: int) -> list[Event]:
    """long-poll：有新事件立刻回；沒有就最多等 wait 秒，逾時回空陣列。"""
    events = events_after(row, cursor)
    if events or wait <= 0:
        return events
    waiter = _waiters.setdefault(row.id, asyncio.Event())
    try:
        await asyncio.wait_for(waiter.wait(), timeout=wait)
    except asyncio.TimeoutError:
        return []
    return events_after(row, cursor)


def ack(row: repo.MailboxRow, cursor: int) -> None:
    row.acked_cursor = max(row.acked_cursor, min(cursor, row.next_cursor - 1))
    row.events = [e for e in row.events if e.cursor > row.acked_cursor]


def purge_expired() -> None:
    """背景工作：刪過期事件與閒置 180 天的信箱。"""
    t = now()
    for mid, row in list(repo.mailboxes.items()):
        if t - row.last_seen_at > MAILBOX_IDLE_TTL:
            del repo.mailboxes[mid]
            continue
        row.events = [e for e in row.events if e.expires_at > t]
