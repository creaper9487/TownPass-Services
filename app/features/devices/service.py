"""推播裝置登記。

- 同一個 token 重複登記 = 更新；如果原本登記在別的信箱（例如重灌 App 後換了信箱），移到新信箱，
  避免收到舊信箱的通知。
- 每個信箱最多 max_devices_per_mailbox 台，超過時移除最久沒更新的。
- FCM 回報 token 失效時由 notification 呼叫 remove()。
"""

from app.config import get_settings
from app.features.devices import repository as repo
from app.tools.timeutil import now


def register(mailbox_id: str, platform: str, token: str) -> None:
    repo.upsert(repo.DeviceRow(token, mailbox_id, platform, now()))
    mine = repo.by_mailbox(mailbox_id)
    for old in mine[: max(0, len(mine) - get_settings().max_devices_per_mailbox)]:
        repo.delete(old.token)


def unregister(mailbox_id: str, token: str) -> None:
    """只能取消自己信箱的裝置；不存在也當成功（冪等）。"""
    row = repo.get(token)
    if row and row.mailbox_id == mailbox_id:
        repo.delete(token)


def tokens_of(mailbox_id: str) -> list[str]:
    return [d.token for d in repo.by_mailbox(mailbox_id)]


def remove(token: str) -> None:
    repo.delete(token)
