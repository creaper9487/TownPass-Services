"""送件佇列（記憶體版）。對應規格「forward_job」，最長 24 小時。

TODO: 正式版 payload 要用 KMS 信封加密；目前只存在記憶體、重啟即消失。
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ForwardJob:
    reservation_id: str
    payload: dict  # ⚠ 含個資
    attempts: int
    state: str  # pending / sent / failed
    next_try_at: datetime
    expires_at: datetime


jobs: dict[str, ForwardJob] = {}


def reset() -> None:
    jobs.clear()
