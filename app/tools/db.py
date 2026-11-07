"""本機 SQLite 資料庫（標準函式庫 sqlite3，不用另外裝）。

存的東西（全部不含個資）：
    devices        推播裝置（FCM token ↔ 信箱）
    push_log       每一則推播的紀錄（測試時看推了什麼、結果如何）
    mailboxes      匿名信箱
    events         信箱事件（通知 / 預約狀態）
    reservations   預約（不含聯絡資料）
    idempotency    Idempotency-Key 對應的預約
    subscriptions  到貨通知
    stock          各品項庫存 + meta 裡的 stock_version
    hook_events    中心 webhook 已處理過的 event_id（去重）
server 重啟資料都還在；要清空就刪掉 DB 檔（預設 data/local.db）。

檔案位置：設定 DB_PATH（預設 data/local.db，已加入 .gitignore）。
server 與 CLI 是不同 process，但讀寫同一個檔案，所以 CLI 看得到 App 登記的裝置。
"""

import sqlite3
import threading
from contextlib import contextmanager
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
    result      TEXT NOT NULL       -- ok / invalid_token / retry / failed / local(=只記錄在本機，沒送到手機)
);

CREATE TABLE IF NOT EXISTS mailboxes (
    id            TEXT PRIMARY KEY,
    key_hash      TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    last_seen_at  TEXT NOT NULL,
    next_cursor   INTEGER NOT NULL DEFAULT 1,
    acked_cursor  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS events (
    mailbox_id  TEXT NOT NULL,
    cursor      INTEGER NOT NULL,
    id          TEXT NOT NULL,
    type        TEXT NOT NULL,
    ts          TEXT NOT NULL,
    ref         TEXT NOT NULL,   -- JSON
    data        TEXT NOT NULL,   -- JSON
    expires_at  TEXT NOT NULL,
    PRIMARY KEY (mailbox_id, cursor)
);

CREATE TABLE IF NOT EXISTS reservations (
    id               TEXT PRIMARY KEY,
    access_key_hash  TEXT NOT NULL,
    mailbox_id       TEXT NOT NULL,
    service          TEXT NOT NULL,
    center_id        TEXT NOT NULL,
    items            TEXT NOT NULL,   -- JSON
    status           TEXT NOT NULL,
    version          INTEGER NOT NULL,
    pickup_deadline  TEXT,
    pickup_dates     TEXT NOT NULL,   -- JSON
    forward_state    TEXT NOT NULL,
    created_at       TEXT NOT NULL,
    updated_at       TEXT NOT NULL,
    reminders_sent   TEXT NOT NULL    -- JSON
);
CREATE INDEX IF NOT EXISTS idx_reservations_status ON reservations(status);

CREATE TABLE IF NOT EXISTS idempotency (
    key             TEXT PRIMARY KEY,
    body_hash       TEXT NOT NULL,
    reservation_id  TEXT NOT NULL,
    access_key      TEXT NOT NULL,   -- 重送同一個請求時要回同一把 key
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS subscriptions (
    seq          INTEGER PRIMARY KEY AUTOINCREMENT,   -- 候補順序
    id           TEXT NOT NULL UNIQUE,
    mailbox_id   TEXT NOT NULL,
    variant_id   TEXT NOT NULL,
    category_id  TEXT,
    variant_name   TEXT,   -- 訂閱當下從目錄查到的品項名稱（推播 data 用）
    category_name  TEXT,
    created_at   TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'waiting',   -- waiting（等待中）/ arrived（已到貨）
    arrived_at   TEXT
);

CREATE TABLE IF NOT EXISTS stock (
    variant_id  TEXT PRIMARY KEY,
    stock       INTEGER NOT NULL,
    waiting     INTEGER NOT NULL,
    version     INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS meta (
    key    TEXT PRIMARY KEY,
    value  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notice_seen (
    id          TEXT PRIMARY KEY,      -- 已經看過 / 推過的公告 id（重啟、CLI 都不會重複推）
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hook_events (
    event_id    TEXT PRIMARY KEY,
    created_at  TEXT NOT NULL
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
            _migrate(_conn)
        return _conn


# 舊的 DB 檔缺少的欄位：(表, 欄位, 定義)。新增欄位時加在這裡，舊檔開啟時會自動補上
_COLUMNS = [
    ("subscriptions", "status", "TEXT NOT NULL DEFAULT 'waiting'"),
    ("subscriptions", "arrived_at", "TEXT"),
    ("subscriptions", "variant_name", "TEXT"),
    ("subscriptions", "category_name", "TEXT"),
]


def _migrate(c: sqlite3.Connection) -> None:
    for table, column, ddl in _COLUMNS:
        have = {r["name"] for r in c.execute(f"PRAGMA table_info({table})")}
        if column not in have:
            c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def execute(sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
    with _lock:
        return conn().execute(sql, params)


def query(sql: str, params: tuple | dict = ()) -> list[sqlite3.Row]:
    with _lock:
        return conn().execute(sql, params).fetchall()


@contextmanager
def transaction():
    """多個寫入要一起成功或一起失敗時用：with db.transaction() as c: c.execute(...)"""
    with _lock:
        c = conn()
        c.execute("BEGIN IMMEDIATE")
        try:
            yield c
        except BaseException:
            c.execute("ROLLBACK")
            raise
        c.execute("COMMIT")


def get_meta(key: str, default: str | None = None) -> str | None:
    rows = query("SELECT value FROM meta WHERE key = ?", (key,))
    return rows[0]["value"] if rows else default


def set_meta(key: str, value: str) -> None:
    execute("INSERT INTO meta(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value))


def close() -> None:
    global _conn
    with _lock:
        if _conn is not None:
            _conn.close()
            _conn = None
