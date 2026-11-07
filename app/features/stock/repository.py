"""庫存（SQLite）。每次有品項變動，全域 version +1 並記在該品項上，供 GET /stock?since= 做增量。"""

from dataclasses import dataclass
from datetime import datetime

from app.tools import db
from app.tools.timeutil import now


@dataclass
class StockRow:
    variant_id: str
    stock: int
    waiting: int
    version: int


def _row(r) -> StockRow:
    return StockRow(r["variant_id"], r["stock"], r["waiting"], r["version"])


def get(variant_id: str) -> StockRow | None:
    rows = db.query("SELECT * FROM stock WHERE variant_id = ?", (variant_id,))
    return _row(rows[0]) if rows else None


def all_rows(since: int | None = None) -> list[StockRow]:
    if since is None:
        return [_row(r) for r in db.query("SELECT * FROM stock ORDER BY variant_id")]
    return [_row(r) for r in db.query("SELECT * FROM stock WHERE version > ? ORDER BY variant_id", (since,))]


def current_version() -> int:
    return int(db.get_meta("stock_version", "0"))


def as_of() -> datetime:
    v = db.get_meta("stock_as_of")
    return datetime.fromisoformat(v) if v else now()


def put(variant_id: str, stock: int, waiting: int, c=None) -> int:
    """寫入一個品項並把全域 version +1；回傳新的 version。c = 已開啟的交易（可選）。"""
    if c is None:
        with db.transaction() as c2:
            return put(variant_id, stock, waiting, c2)
    row = c.execute("SELECT value FROM meta WHERE key = 'stock_version'").fetchone()
    version = int(row["value"]) + 1 if row else 1
    c.execute("INSERT INTO meta(key, value) VALUES ('stock_version', ?) "
              "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (str(version),))
    c.execute("INSERT INTO meta(key, value) VALUES ('stock_as_of', ?) "
              "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (now().isoformat(),))
    c.execute("INSERT INTO stock(variant_id, stock, waiting, version) VALUES (?, ?, ?, ?) "
              "ON CONFLICT(variant_id) DO UPDATE SET stock = excluded.stock, waiting = excluded.waiting, "
              "version = excluded.version", (variant_id, stock, waiting, version))
    return version


def reset() -> None:
    with db.transaction() as c:
        c.execute("DELETE FROM stock")
        c.execute("DELETE FROM meta WHERE key IN ('stock_version', 'stock_as_of')")
