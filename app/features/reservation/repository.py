"""預約（SQLite）。欄位對應規格「資料表 reservation」，全部不含個資（聯絡資料不存）。"""

import json
from dataclasses import dataclass, field
from datetime import date, datetime

from app.tools import db


@dataclass
class ReservationRow:
    id: str
    access_key_hash: str
    mailbox_id: str
    service: str
    center_id: str
    items: list[str]
    status: str
    version: int
    pickup_deadline: date | None
    pickup_dates: list[date]
    forward_state: str  # off（不送中心）/ pending / sent / failed
    created_at: datetime
    updated_at: datetime
    reminders_sent: set[str] = field(default_factory=set)


def _row(r) -> ReservationRow:
    return ReservationRow(
        id=r["id"], access_key_hash=r["access_key_hash"], mailbox_id=r["mailbox_id"], service=r["service"],
        center_id=r["center_id"], items=json.loads(r["items"]), status=r["status"], version=r["version"],
        pickup_deadline=date.fromisoformat(r["pickup_deadline"]) if r["pickup_deadline"] else None,
        pickup_dates=[date.fromisoformat(d) for d in json.loads(r["pickup_dates"])],
        forward_state=r["forward_state"], created_at=datetime.fromisoformat(r["created_at"]),
        updated_at=datetime.fromisoformat(r["updated_at"]), reminders_sent=set(json.loads(r["reminders_sent"])),
    )


def _values(row: ReservationRow) -> tuple:
    return (row.access_key_hash, row.mailbox_id, row.service, row.center_id, json.dumps(row.items, ensure_ascii=False),
            row.status, row.version, row.pickup_deadline.isoformat() if row.pickup_deadline else None,
            json.dumps([d.isoformat() for d in row.pickup_dates]), row.forward_state, row.created_at.isoformat(),
            row.updated_at.isoformat(), json.dumps(sorted(row.reminders_sent)), row.id)


def insert(row: ReservationRow, c=None) -> None:
    (c or db).execute(
        "INSERT INTO reservations(access_key_hash, mailbox_id, service, center_id, items, status, version, "
        "pickup_deadline, pickup_dates, forward_state, created_at, updated_at, reminders_sent, id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", _values(row))


def save(row: ReservationRow) -> None:
    db.execute(
        "UPDATE reservations SET access_key_hash=?, mailbox_id=?, service=?, center_id=?, items=?, status=?, "
        "version=?, pickup_deadline=?, pickup_dates=?, forward_state=?, created_at=?, updated_at=?, "
        "reminders_sent=? WHERE id=?", _values(row))


def get(reservation_id: str) -> ReservationRow | None:
    rows = db.query("SELECT * FROM reservations WHERE id = ?", (reservation_id,))
    return _row(rows[0]) if rows else None


def exists(reservation_id: str) -> bool:
    return bool(db.query("SELECT 1 FROM reservations WHERE id = ?", (reservation_id,)))


def all_reservations(limit: int = 200) -> list[ReservationRow]:
    return [_row(r) for r in db.query("SELECT * FROM reservations ORDER BY created_at DESC LIMIT ?", (limit,))]


def booked_borrows() -> list[ReservationRow]:
    return [_row(r) for r in db.query(
        "SELECT * FROM reservations WHERE service = 'borrow' AND status = 'booked' ORDER BY created_at")]


def get_idempotency(key: str) -> tuple[str, str, str] | None:
    rows = db.query("SELECT body_hash, reservation_id, access_key FROM idempotency WHERE key = ?", (key,))
    return (rows[0]["body_hash"], rows[0]["reservation_id"], rows[0]["access_key"]) if rows else None


def put_idempotency(key: str, body_hash: str, reservation_id: str, access_key: str, created_at: str, c=None) -> None:
    (c or db).execute("INSERT INTO idempotency(key, body_hash, reservation_id, access_key, created_at) "
                      "VALUES (?, ?, ?, ?, ?)", (key, body_hash, reservation_id, access_key, created_at))


def reset() -> None:
    with db.transaction() as c:
        c.execute("DELETE FROM reservations")
        c.execute("DELETE FROM idempotency")
