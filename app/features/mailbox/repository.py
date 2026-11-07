"""信箱與事件（記憶體版）。不存任何個資。"""

from dataclasses import dataclass, field
from datetime import datetime

from app.features.mailbox.schemas import Event


@dataclass
class MailboxRow:
    id: str
    key_hash: str
    created_at: datetime
    last_seen_at: datetime
    next_cursor: int = 1
    acked_cursor: int = 0
    events: list[Event] = field(default_factory=list)


mailboxes: dict[str, MailboxRow] = {}


def reset() -> None:
    mailboxes.clear()
