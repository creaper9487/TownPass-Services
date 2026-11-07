"""出站：通知台北通推播閘道「某信箱有新事件」。

推播只負責叫醒 App，內容只有 mailbox_id 與 cursor，不帶姓名、預約編號、輔具名稱。
POST {PUSH_GATEWAY_URL}
    {"type": "mailbox.updated", "mailbox_id": "mb_xxx", "cursor": 128, "collapse_key": "mb_xxx"}
Header：X-Timestamp、X-Signature（HMAC-SHA256），逾時 3 秒，失敗重試 1s/4s/16s/1m/5m。

PUSH_GATEWAY_URL 未設定時直接略過（App 下次打開會用 cursor 補拉）。
"""

import asyncio
import json
import time

from app.config import get_settings
from app.tools.http_client import get_http_client
from app.tools.logger import get_logger
from app.tools.security import sign

logger = get_logger(__name__)

RETRY_DELAYS = [1, 4, 16, 60, 300]


async def send_wakeup(mailbox_id: str, cursor: int) -> bool:
    settings = get_settings()
    if not settings.push_gateway_url:
        return False

    body = json.dumps(
        {"type": "mailbox.updated", "mailbox_id": mailbox_id, "cursor": cursor, "collapse_key": mailbox_id}
    ).encode()

    for attempt, delay in enumerate([0, *RETRY_DELAYS]):
        if delay:
            await asyncio.sleep(delay)
        ts = str(int(time.time()))
        headers = {
            "Content-Type": "application/json",
            "X-Timestamp": ts,
            "X-Signature": sign(settings.push_secret, ts, body),
        }
        try:
            res = await get_http_client().post(settings.push_gateway_url, content=body, headers=headers, timeout=3.0)
            if res.status_code < 300:
                return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("push attempt %d failed: %s", attempt + 1, type(exc).__name__)
    return False


def schedule_wakeup(mailbox_id: str, cursor: int) -> None:
    """不阻塞呼叫端，背景送出喚醒。"""
    try:
        asyncio.get_running_loop().create_task(send_wakeup(mailbox_id, cursor))
    except RuntimeError:
        pass  # 沒有 event loop（例如同步測試）時略過
