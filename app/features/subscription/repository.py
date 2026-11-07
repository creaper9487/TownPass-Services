"""到貨通知訂閱（SQLite）。seq = 候補順序。"""

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


def _row(r) -> SubscriptionRow:
    return SubscriptionRow(r["id"], r["mailbox_id"], r["variant_id"], r["category_id"],
                           datetime.fromisoformat(r["created_at"]))


def insert(row: SubscriptionRow) -> None:
    db.execute("INSERT INTO subscriptions(id, mailbox_id, variant_id, category_id, created_at) VALUES (?, ?, ?, ?, ?)",
               (row.id, row.mailbox_id, row.variant_id, row.category_id, row.created_at.isoformat()))


def get(sub_id: str) -> SubscriptionRow | None:
    rows = db.query("SELECT * FROM subscriptions WHERE id = ?", (sub_id,))
    return _row(rows[0]) if rows else None


def by_mailbox(mailbox_id: str) -> list[SubscriptionRow]:
    return [_row(r) for r in db.query("SELECT * FROM subscriptions WHERE mailbox_id = ? ORDER BY seq", (mailbox_id,))]


def waiting_for(variant_id: str, limit: int) -> list[SubscriptionRow]:
    return [_row(r) for r in db.query(
        "SELECT * FROM subscriptions WHERE variant_id = ? ORDER BY seq LIMIT ?", (variant_id, limit))]


def subscribed_variants() -> list[str]:
    return [r["variant_id"] for r in db.query("SELECT DISTINCT variant_id FROM subscriptions")]


def delete(sub_id: str) -> None:
    db.execute("DELETE FROM subscriptions WHERE id = ?", (sub_id,))


def reset() -> None:
    db.execute("DELETE FROM subscriptions")
