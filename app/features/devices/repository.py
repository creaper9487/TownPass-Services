"""已登記的推播裝置（記憶體版）。token → 裝置；一個 token 只屬於一個信箱。"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class DeviceRow:
    token: str
    mailbox_id: str
    platform: str
    updated_at: datetime


devices: dict[str, DeviceRow] = {}


def reset() -> None:
    devices.clear()
