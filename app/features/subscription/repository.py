"""到貨通知訂閱（SQLite）。seq = 候補順序；status：waiting（等待中）→ arrived（已到貨）。"""

from dataclasses import dataclass
from datetime import datetime

from app.tools import db


@dataclass
class SubscriptionRow:
    id: str
    mailbox_id: str
    variant_id: str
    category_id: str | None
    created_at: datetime
    status: str = "waiting"
    arrived_at: datetime | None = None


def _row(r) -> SubscriptionRow:
    return SubscriptionRow(r["id"], r["mailbox_id"], r["variant_id"], r["category_id"],
                           datetime.fromisoformat(r["created_at"]), r["status"],
                           datetime.fromisoformat(r["arrived_at"]) if r["arrived_at"] else None)


def insert(row: SubscriptionRow) -> None:
    db.execute("INSERT INTO subscriptions(id, mailbox_id, variant_id, category_id, created_at, status) "
               "VALUES (?, ?, ?, ?, ?, 'waiting')",
               (row.id, row.mailbox_id, row.variant_id, row.category_id, row.created_at.isoformat()))


def get(sub_id: str) -> SubscriptionRow | None:
    rows = db.query("SELECT * FROM subscriptions WHERE id = ?", (sub_id,))
    return _row(rows[0]) if rows else None


def by_mailbox(mailbox_id: str, status: str | None = None) -> list[SubscriptionRow]:
    if status:
        return [_row(r) for r in db.query(
            "SELECT * FROM subscriptions WHERE mailbox_id = ? AND status = ? ORDER BY seq", (mailbox_id, status))]
    return [_row(r) for r in db.query("SELECT * FROM subscriptions WHERE mailbox_id = ? ORDER BY seq", (mailbox_id,))]


def waiting_with_stock() -> list[tuple[SubscriptionRow, int]]:
    """等待中、而且該品項現在有庫存的訂閱（依候補順序），附上目前庫存數。"""
    return [(_row(r), r["stock"]) for r in db.query(
        "SELECT s.*, k.stock AS stock FROM subscriptions s JOIN stock k ON k.variant_id = s.variant_id "
        "WHERE s.status = 'waiting' AND k.stock > 0 ORDER BY s.seq")]


def waiting(variant_id: str | None = None, mailbox_id: str | None = None) -> list[SubscriptionRow]:
    sql, params = "SELECT * FROM subscriptions WHERE status = 'waiting'", []
    if variant_id:
        sql, params = sql + " AND variant_id = ?", params + [variant_id]
    if mailbox_id:
        sql, params = sql + " AND mailbox_id = ?", params + [mailbox_id]
    return [_row(r) for r in db.query(sql + " ORDER BY seq", tuple(params))]


def mark_arrived(sub_id: str, ts: datetime) -> bool:
    """waiting → arrived；已經是 arrived 回 False（不重複推播）。"""
    cur = db.execute("UPDATE subscriptions SET status = 'arrived', arrived_at = ? WHERE id = ? AND status = 'waiting'",
                     (ts.isoformat(), sub_id))
    return cur.rowcount == 1


def subscribed_variants() -> list[str]:
    return [r["variant_id"] for r in db.query("SELECT DISTINCT variant_id FROM subscriptions WHERE status = 'waiting'")]


def delete(sub_id: str) -> None:
    db.execute("DELETE FROM subscriptions WHERE id = ?", (sub_id,))


def reset() -> None:
    db.execute("DELETE FROM subscriptions")
