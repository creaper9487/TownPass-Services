"""信箱與事件（SQLite）。不存任何個資。"""

import json
from dataclasses import dataclass
from datetime import datetime

from app.features.mailbox.schemas import Event
from app.tools import db


@dataclass
class MailboxRow:
    id: str
    key_hash: str
    created_at: datetime
    last_seen_at: datetime
    next_cursor: int = 1
    acked_cursor: int = 0


def _mb(r) -> MailboxRow:
    return MailboxRow(r["id"], r["key_hash"], datetime.fromisoformat(r["created_at"]),
                      datetime.fromisoformat(r["last_seen_at"]), r["next_cursor"], r["acked_cursor"])


def _ev(r) -> Event:
    return Event(cursor=r["cursor"], id=r["id"], type=r["type"], ts=r["ts"], ref=json.loads(r["ref"]),
                 data=json.loads(r["data"]), expires_at=r["expires_at"])


def insert(row: MailboxRow) -> None:
    db.execute("INSERT INTO mailboxes(id, key_hash, created_at, last_seen_at, next_cursor, acked_cursor) "
               "VALUES (?, ?, ?, ?, ?, ?)", (row.id, row.key_hash, row.created_at.isoformat(),
                                             row.last_seen_at.isoformat(), row.next_cursor, row.acked_cursor))


def get(mailbox_id: str) -> MailboxRow | None:
    rows = db.query("SELECT * FROM mailboxes WHERE id = ?", (mailbox_id,))
    return _mb(rows[0]) if rows else None


def all_mailboxes() -> list[MailboxRow]:
    return [_mb(r) for r in db.query("SELECT * FROM mailboxes ORDER BY created_at")]


def touch(mailbox_id: str, ts: datetime) -> None:
    db.execute("UPDATE mailboxes SET last_seen_at = ? WHERE id = ?", (ts.isoformat(), mailbox_id))


def add_event(mailbox_id: str, make_event) -> Event | None:
    """取下一個 cursor、寫入事件（同一個交易，避免 cursor 重複）。make_event(cursor) -> Event"""
    with db.transaction() as c:
        r = c.execute("SELECT next_cursor FROM mailboxes WHERE id = ?", (mailbox_id,)).fetchone()
        if r is None:
            return None
        event: Event = make_event(r["next_cursor"])
        c.execute("INSERT INTO events(mailbox_id, cursor, id, type, ts, ref, data, expires_at) "
                  "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (mailbox_id, event.cursor, event.id, event.type, event.ts.isoformat(),
                   json.dumps(event.ref, ensure_ascii=False), json.dumps(event.data, ensure_ascii=False),
                   event.expires_at.isoformat()))
        c.execute("UPDATE mailboxes SET next_cursor = next_cursor + 1 WHERE id = ?", (mailbox_id,))
        return event


def events_after(mailbox_id: str, cursor: int, now_iso: str) -> list[Event]:
    return [_ev(r) for r in db.query(
        "SELECT * FROM events WHERE mailbox_id = ? AND cursor > ? AND expires_at > ? ORDER BY cursor",
        (mailbox_id, cursor, now_iso))]


def count_events(mailbox_id: str) -> int:
    return db.query("SELECT COUNT(*) AS n FROM events WHERE mailbox_id = ?", (mailbox_id,))[0]["n"]


def ack(mailbox_id: str, cursor: int) -> None:
    with db.transaction() as c:
        c.execute("UPDATE mailboxes SET acked_cursor = MAX(acked_cursor, MIN(?, next_cursor - 1)) WHERE id = ?",
                  (cursor, mailbox_id))
        c.execute("DELETE FROM events WHERE mailbox_id = ? AND cursor <= "
                  "(SELECT acked_cursor FROM mailboxes WHERE id = ?)", (mailbox_id, mailbox_id))


def purge(now_iso: str, idle_before_iso: str) -> None:
    with db.transaction() as c:
        c.execute("DELETE FROM events WHERE expires_at <= ?", (now_iso,))
        c.execute("DELETE FROM events WHERE mailbox_id IN (SELECT id FROM mailboxes WHERE last_seen_at < ?)",
                  (idle_before_iso,))
        c.execute("DELETE FROM mailboxes WHERE last_seen_at < ?", (idle_before_iso,))


def reset() -> None:
    with db.transaction() as c:
        c.execute("DELETE FROM events")
        c.execute("DELETE FROM mailboxes")
