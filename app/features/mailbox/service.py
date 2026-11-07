"""匿名信箱：所有通知與預約狀態事件都寫進信箱，前端用 cursor pull。

- 寫入事件後，喚醒正在 long-poll / SSE 等待的連線，並通知推播閘道（只帶 id + cursor）。
- 事件保留 30 天；ack 之後可清除。
"""

import asyncio
from datetime import timedelta
from typing import Any

from app.features.mailbox import repository as repo
from app.features.mailbox.schemas import Event, EventType, MailboxCreated
from app.tools import exceptions as E
from app.tools import push
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
                 data: dict[str, Any] | None = None) -> Event | None:
    row = repo.mailboxes.get(mailbox_id)
    if row is None:
        return None
    ts = now()
    event = Event(cursor=row.next_cursor, id=new_id("ev"), type=type, ts=ts,
                  ref=ref or {}, data=data or {}, expires_at=ts + EVENT_TTL)
    row.next_cursor += 1
    row.events.append(event)
    _signal(mailbox_id)
    push.schedule_wakeup(mailbox_id, event.cursor)
    return event


def broadcast(type: EventType, data: dict[str, Any]) -> int:
    """service.notice：公告廣播給所有信箱。"""
    return sum(1 for mid in list(repo.mailboxes) if append_event(mid, type, data=data))


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
