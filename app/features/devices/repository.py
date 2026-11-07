"""推播裝置（SQLite，見 app/tools/db.py）。token → 裝置；一個 token 只屬於一個信箱。"""

from dataclasses import dataclass
from datetime import datetime

from app.tools import db


@dataclass
class DeviceRow:
    token: str
    mailbox_id: str
    platform: str
    updated_at: datetime


def _row(r) -> DeviceRow:
    return DeviceRow(r["token"], r["mailbox_id"], r["platform"], datetime.fromisoformat(r["updated_at"]))


def upsert(row: DeviceRow) -> None:
    db.execute(
        "INSERT INTO devices(token, mailbox_id, platform, updated_at) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(token) DO UPDATE SET mailbox_id=excluded.mailbox_id, platform=excluded.platform, "
        "updated_at=excluded.updated_at",
        (row.token, row.mailbox_id, row.platform, row.updated_at.isoformat()),
    )


def get(token: str) -> DeviceRow | None:
    rows = db.query("SELECT * FROM devices WHERE token = ?", (token,))
    return _row(rows[0]) if rows else None


def by_mailbox(mailbox_id: str) -> list[DeviceRow]:
    """依更新時間由舊到新。"""
    return [_row(r) for r in db.query(
        "SELECT * FROM devices WHERE mailbox_id = ? ORDER BY updated_at", (mailbox_id,))]


def all_devices() -> list[DeviceRow]:
    return [_row(r) for r in db.query("SELECT * FROM devices ORDER BY updated_at DESC")]


def delete(token: str) -> None:
    db.execute("DELETE FROM devices WHERE token = ?", (token,))


def reset() -> None:
    db.execute("DELETE FROM devices")
