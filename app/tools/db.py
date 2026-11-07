"""本機 SQLite 資料庫（標準函式庫 sqlite3，不用另外裝）。

目前存：
    devices    推播裝置（FCM token ↔ 信箱），server 重啟也不會不見
    push_log   每一則推播的紀錄（測試時看推了什麼、結果如何）

檔案位置：設定 DB_PATH（預設 data/local.db，已加入 .gitignore）。
server 與 CLI 是不同 process，但讀寫同一個檔案，所以 CLI 看得到 App 登記的裝置。
"""

import sqlite3
import threading
from pathlib import Path

from app.config import get_settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS devices (
    token       TEXT PRIMARY KEY,
    mailbox_id  TEXT NOT NULL,
    platform    TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_devices_mailbox ON devices(mailbox_id);

CREATE TABLE IF NOT EXISTS push_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  TEXT NOT NULL,
    target      TEXT NOT NULL,      -- token 前 12 碼… 或 topic:xxx
    mailbox_id  TEXT,
    type        TEXT,
    title       TEXT,
    body        TEXT,
    data        TEXT,               -- JSON
    result      TEXT NOT NULL       -- ok / invalid_token / retry / failed / disabled(=沒設定 FCM，只記錄)
);
"""

_conn: sqlite3.Connection | None = None
_lock = threading.RLock()


def conn() -> sqlite3.Connection:
    global _conn
    with _lock:
        if _conn is None:
            path = get_settings().db_path
            if path != ":memory:":
                Path(path).parent.mkdir(parents=True, exist_ok=True)
            _conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
            _conn.row_factory = sqlite3.Row
            _conn.execute("PRAGMA journal_mode=WAL") if path != ":memory:" else None
            _conn.executescript(SCHEMA)
        return _conn


def execute(sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
    with _lock:
        return conn().execute(sql, params)


def query(sql: str, params: tuple | dict = ()) -> list[sqlite3.Row]:
    with _lock:
        return conn().execute(sql, params).fetchall()


def close() -> None:
    global _conn
    with _lock:
        if _conn is not None:
            _conn.close()
            _conn = None
