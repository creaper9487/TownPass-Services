"""主動推播：事件寫進信箱後，推播到這個信箱登記的所有裝置。

流程：
    mailbox.append_event() → notify_event() → 組文案 → 對每個 token 發 FCM
        - 成功：結束
        - token 失效：刪掉這個裝置
        - 暫時失敗（429 / 5xx / 網路）：放進重試佇列，由 push_check 每 N 分鐘重試（最多 3 次）
    公告（service.notice）不逐台發，改發 FCM topic，一次送給所有訂閱的 App。

FCM data：{type, event_id, reservation_id?, variant_id?}
    Flutter 點推播時：有 reservation_id 開 /assistive/reservations/{id}，其他開 /assistive。
"""

import asyncio
import json
from dataclasses import dataclass

from app import config
from app.features.devices import service as devices_service
from app.features.mailbox.schemas import Event
from app.features.notification import texts
from app.tools import db, fcm
from app.tools.logger import get_logger
from app.tools.timeutil import now

logger = get_logger(__name__)

MAX_RETRIES = 3


@dataclass
class PendingPush:
    message: dict
    token: str | None  # None = topic
    attempts: int
    mailbox_id: str | None = None


_retry_queue: list[PendingPush] = []
_tasks: set[asyncio.Task] = set()


def _spawn(coro) -> None:
    try:
        task = asyncio.get_running_loop().create_task(coro)
    except RuntimeError:
        coro.close()  # 沒有 event loop（同步情境）時略過，事件仍在信箱可補拉
        return
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)


def _event_text(event: Event) -> tuple[str, str]:
    from app.features.reservation import repository as reservation_repo

    rid = event.ref.get("reservation_id")
    row = reservation_repo.get(rid) if rid else None
    return texts.build(
        event.type,
        deadline=event.data.get("pickup_deadline") or (row.pickup_deadline if row else None),
        center_id=row.center_id if row else None,
        notice_title=event.data.get("title"),
    )


def _data(event: Event) -> dict:
    return {
        "type": event.type,
        "event_id": event.id,
        "reservation_id": event.ref.get("reservation_id"),
        "variant_id": event.ref.get("variant_id"),
    }


def log_push(push: PendingPush, result: "fcm.SendResult") -> None:
    """每一則推播都記到本機 DB 的 push_log（CLI `outbox` 可以看）。token 只存前 12 碼。"""
    m = push.message["message"]
    target = f"{push.token[:12]}…" if push.token else f"topic:{m.get('topic')}"
    db.execute(
        "INSERT INTO push_log(created_at, target, mailbox_id, type, title, body, data, result) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (now().isoformat(), target, push.mailbox_id, m["data"].get("type"), m["notification"]["title"],
         m["notification"]["body"], json.dumps(m["data"], ensure_ascii=False), result.value),
    )


async def _deliver(push: PendingPush) -> None:
    result = await fcm.send(push.message)
    log_push(push, result)
    if result == fcm.SendResult.INVALID_TOKEN and push.token:
        devices_service.remove(push.token)
    elif result == fcm.SendResult.RETRY:
        push.attempts += 1
        if push.attempts < MAX_RETRIES:
            _retry_queue.append(push)
        else:
            logger.warning("push dropped after %d attempts", push.attempts)


def notify_event(mailbox_id: str, event: Event) -> None:
    """mailbox 寫入事件後呼叫。不阻塞呼叫端。"""
    # 沒設定 FCM 也照樣跑流程：fcm.send 回 local、記進 push_log，方便看推了什麼
    title, body = _event_text(event)
    for token in devices_service.tokens_of(mailbox_id):
        msg = fcm.build_message(title=title, body=body, data=_data(event), token=token)
        _spawn(_deliver(PendingPush(msg, token, 0, mailbox_id)))


def notify_topic(event: Event) -> None:
    """公告：發一次到 topic，所有訂閱 assistive-notice 的 App 都會收到。"""
    title, body = _event_text(event)
    msg = fcm.build_message(title=title, body=body, data=_data(event), topic=config.FCM_NOTICE_TOPIC)
    _spawn(_deliver(PendingPush(msg, None, 0)))


async def retry_failed() -> int:
    """push_check 每 N 分鐘呼叫：重送暫時失敗的推播。"""
    pending = _retry_queue[:]
    _retry_queue.clear()
    await asyncio.gather(*(_deliver(p) for p in pending))
    return len(pending)


async def drain() -> None:
    """測試用：等所有背景推播送完。"""
    while _tasks:
        await asyncio.gather(*list(_tasks), return_exceptions=True)


# ---------------- 測試用：直接推播（CLI、測試面板共用）----------------
async def send_direct(targets: list[tuple[str, str | None]], type: str, *, reservation_id: str | None = None,
                      variant_id: str | None = None, deadline: str | None = None, center_id: str | None = None,
                      notice_title: str | None = None) -> list[dict]:
    """不經過任何狀態，直接對 (token, mailbox_id) 發一則指定類型的通知；回傳每一台的結果。"""
    from app.features.devices import repository as devices_repo
    from app.tools.security import new_id

    title, body = texts.build(type, deadline=deadline, center_id=center_id, notice_title=notice_title)
    data = {"type": type, "event_id": new_id("ev"), "reservation_id": reservation_id, "variant_id": variant_id}
    results = []
    for token, mailbox_id in targets:
        push = PendingPush(fcm.build_message(title=title, body=body, data=data, token=token), token, 0, mailbox_id)
        result = await fcm.send(push.message)
        log_push(push, result)
        if result == fcm.SendResult.INVALID_TOKEN:
            devices_repo.delete(token)
        results.append({"token": token[:16] + "…", "mailbox_id": mailbox_id, "result": result.value,
                        "title": title, "body": body})
    return results


async def send_topic(title: str) -> dict:
    from app.tools.security import new_id

    t, body = texts.build("service.notice", notice_title=title)
    msg = fcm.build_message(title=t, body=body, data={"type": "service.notice", "event_id": new_id("ev")},
                            topic=config.FCM_NOTICE_TOPIC)
    result = await fcm.send(msg)
    log_push(PendingPush(msg, None, 0), result)
    return {"target": f"topic:{config.FCM_NOTICE_TOPIC}", "result": result.value, "title": t, "body": body}


def reset() -> None:
    _retry_queue.clear()
