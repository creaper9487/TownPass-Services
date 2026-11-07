"""庫存資料（記憶體版）。之後換資料庫只要改這個檔。

每次有品項變動，全域 version +1，並記在該品項上，供 GET /stock?since= 做增量。
"""

from dataclasses import dataclass
from datetime import datetime

from app.tools.timeutil import now


@dataclass
class StockRow:
    variant_id: str
    stock: int
    waiting: int
    version: int


rows: dict[str, StockRow] = {}
state = {"version": 0, "as_of": now()}


def bump_version() -> int:
    state["version"] += 1
    state["as_of"] = now()
    return state["version"]


def current_version() -> int:
    return state["version"]


def as_of() -> datetime:
    return state["as_of"]


def reset() -> None:
    rows.clear()
    state["version"] = 0
    state["as_of"] = now()
