"""簡單的記憶體 TTL 快取，給 catalog / centers / calendar 用。"""

import hashlib
import json
import time
from typing import Any


class TTLCache:
    def __init__(self, ttl_seconds: int):
        self.ttl = ttl_seconds
        self._data: dict[Any, tuple[float, Any]] = {}

    def get(self, key: Any = None) -> Any | None:
        hit = self._data.get(key)
        if hit and hit[0] > time.monotonic():
            return hit[1]
        return None

    def set(self, value: Any, key: Any = None) -> None:
        self._data[key] = (time.monotonic() + self.ttl, value)

    def clear(self) -> None:
        self._data.clear()


def etag_of(data: Any) -> str:
    raw = json.dumps(data, sort_keys=True, default=str, ensure_ascii=False).encode()
    return '"' + hashlib.sha256(raw).hexdigest()[:16] + '"'
