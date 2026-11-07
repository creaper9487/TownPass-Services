"""時間工具：全系統一律使用台北時間（+08:00），ISO 8601 格式。

台灣沒有日光節約時間，用固定 offset 即可（也避免 Windows 缺 tzdata）。
"""

from datetime import date, datetime, timedelta, timezone

TAIPEI = timezone(timedelta(hours=8))


def now() -> datetime:
    return datetime.now(TAIPEI)


def today() -> date:
    return now().date()
