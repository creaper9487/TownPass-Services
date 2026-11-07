"""測試模式專用 API（/_test/*）。TEST_MODE=false 時全部回 404。

用來在不需要中心系統、不需要等時間的情況下，直接觸發各種狀態與推播：
    GET  /_test/state                          目前狀態總覽（信箱、預約、裝置、最近推播）
    POST /_test/scenario                       一鍵：建信箱 + 登記裝置 + 借用預約（會推「預約成功」）
    POST /_test/reservations/{id}/trigger      讓預約進入某個狀態（會推對應通知）
    POST /_test/stock                          設定某款庫存（0 → >0 會推「到貨通知」）
    POST /_test/notices                        發一則公告（推「服務公告」）
    POST /_test/sync                           立刻抓一次資料（模擬官網變化）→ 有變化就推播
    POST /_test/devices                        直接登記一支手機的 FCM token（不用 mailbox_key）
    POST /_test/push                           不改任何狀態，直接推一則指定類型的通知
    GET  /_test/events?mailbox_id=             看某信箱收到的事件（= App pull 會拿到的內容）
    GET  /_test/panel                          測試面板網頁：按按鈕直接推送、看結果
CLI（python -m app.cli）也是在打這些 API。
開關：app/config.py 的 API_ENABLED["test"] + .env 的 TEST_MODE=true。
"""

import json
from datetime import timedelta
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app import config
from app.features.devices import repository as devices_repo
from app.features.devices import service as devices_service
from app.features.mailbox import repository as mailbox_repo
from app.features.mailbox import service as mailbox_service
from app.features.notification import service as notification_service
from app.features.reservation import repository as reservation_repo
from app.features.reservation import service as reservation_service
from app.features.reservation.schemas import ReservationCreate
from app.features.stock import repository as stock_repo
from app.features.stock import service as stock_service
from app.tools import db, fcm
from app.tools import exceptions as E
from app.tools.crawlers.schemas import StockItem
from app.tools.security import new_id
from app.tools.timeutil import today


def require_test_mode() -> None:
    if not config.test_api_enabled():
        raise HTTPException(status_code=404)


router = APIRouter(prefix="/_test", tags=["test mode"], dependencies=[Depends(require_test_mode)])

TEST_CONTACT = {"name": "測試使用者", "mobile": "0900000000", "gender": "X"}


PANEL_HTML = Path(__file__).resolve().parent.parent / "static" / "test_panel.html"

EVENT_TYPES = ["reservation.booked", "reservation.pickup_reminder", "reservation.expired", "reservation.confirmed",
               "reservation.completed", "reservation.cancelled", "stock.arrived", "service.notice"]


@router.get("/panel", response_class=HTMLResponse, summary="測試面板（瀏覽器打開）")
async def panel():
    return HTMLResponse(PANEL_HTML.read_text(encoding="utf-8"))


@router.get("/state", summary="狀態總覽")
async def state(limit: int = 20):
    return {
        "test_mode": True,
        "fcm_enabled": fcm.is_enabled(),
        "api_enabled": config.API_ENABLED,
        "intervals": {"stock_sync_seconds": config.STOCK_SYNC_SECONDS, "push_check_minutes": config.PUSH_CHECK_MINUTES},
        "stock_version": stock_repo.current_version(),
        "mailboxes": [{"mailbox_id": m.id, "events": mailbox_repo.count_events(m.id), "next_cursor": m.next_cursor,
                       "devices": len(devices_repo.by_mailbox(m.id))} for m in mailbox_repo.all_mailboxes()],
        "reservations": [{"id": r.id, "service": r.service, "status": r.status, "center_id": r.center_id,
                          "mailbox_id": r.mailbox_id, "items": r.items, "pickup_deadline": r.pickup_deadline,
                          "forward_state": r.forward_state} for r in reservation_repo.all_reservations()],
        "devices": [{"token": d.token[:12] + "…", "mailbox_id": d.mailbox_id, "updated_at": d.updated_at}
                    for d in devices_repo.all_devices()],
        "subscriptions": [dict(r) for r in db.query(
            "SELECT s.id, s.mailbox_id, s.variant_id, COALESCE(k.stock, 0) AS stock, "
            "(SELECT COUNT(*) FROM devices d WHERE d.mailbox_id = s.mailbox_id) AS devices "
            "FROM subscriptions s LEFT JOIN stock k ON k.variant_id = s.variant_id ORDER BY s.seq")],
        "recent_pushes": [dict(r) | {"data": json.loads(r["data"] or "{}")} for r in db.query(
            "SELECT * FROM push_log ORDER BY id DESC LIMIT ?", (limit,))],
    }


class ScenarioIn(BaseModel):
    token: str | None = Field(None, description="手機的 FCM token；不給就登記本機假裝置（推播只記錄在本機）")
    variant_id: str | None = Field(None, description="要借哪一款；不給就挑第一個有庫存的")


@router.post("/scenario", summary="一鍵建立：信箱 + 裝置 + 借用預約")
async def scenario(body: ScenarioIn):
    if stock_repo.current_version() == 0:
        await stock_service.sync_from_source()
    mb = mailbox_service.create()
    token = body.token or fcm.local_token(mb.mailbox_id)
    devices_service.register(mb.mailbox_id, "fcm", token)
    variant_id = body.variant_id or next((r.variant_id for r in stock_repo.all_rows()
                                         if r.stock > 0 and r.variant_id not in config.BLOCKED_VARIANTS), None)
    if variant_id is None:
        raise E.out_of_stock(0, 0)
    last_error = None
    for center_id in ("heyi", "south", "west"):  # 挑一間取貨期限內有開館的
        payload = ReservationCreate(service="borrow", mailbox_id=mb.mailbox_id, center_id=center_id,
                                    items=[variant_id], contact=TEST_CONTACT)
        try:
            r = await reservation_service.create(payload, new_id("test"))
            break
        except E.AppError as exc:
            if exc.code != "PICKUP_WINDOW_CLOSED":
                raise
            last_error = exc
    else:
        raise last_error
    return {"mailbox_id": mb.mailbox_id, "mailbox_key": mb.mailbox_key, "device_token": token,
            "reservation": r.model_dump(mode="json"), "center_id": center_id}


class TriggerIn(BaseModel):
    event: Literal["pickup_reminder", "expired", "confirmed", "completed", "cancelled"]


@router.post("/reservations/{reservation_id}/trigger", summary="讓預約進入某個狀態並推播")
async def trigger(reservation_id: str, body: TriggerIn):
    row = reservation_repo.get(reservation_id)
    if row is None:
        raise E.not_found("預約")
    match body.event:
        case "pickup_reminder":
            mailbox_service.append_event(row.mailbox_id, "reservation.pickup_reminder",
                                         ref={"reservation_id": row.id},
                                         data={"pickup_deadline": (row.pickup_deadline or today()).isoformat()})
        case "expired":
            if row.service != "borrow" or row.status != "booked":
                raise E.AppError("INVALID_STATE", 409, f"只有 booked 的借用可以逾期（目前 {row.status}）")
            row.pickup_deadline = today() - timedelta(days=1)  # 假裝期限已過，跑真正的逾期流程
            reservation_repo.save(row)
            await reservation_service.expire_overdue()
        case _:
            await reservation_service.apply_center_status(row.id, body.event)
    row = reservation_repo.get(reservation_id)  # 重新讀 DB 拿最新狀態
    return {"id": row.id, "status": row.status, "version": row.version}


@router.post("/sync", summary="立刻抓一次資料；測試模式下假資料會變化（到貨、新公告），有變化就推播")
async def sync():
    from app.features import jobs

    return await jobs.sync_now()


class StockIn(BaseModel):
    variant_id: str
    stock: int = Field(..., ge=0)
    waiting: int = Field(0, ge=0)


@router.post("/stock", summary="設定某款庫存（0 → >0 會推到貨通知給訂閱者）")
async def set_stock(body: StockIn):
    changed = await stock_service.apply_items([StockItem(**body.model_dump())])
    return {"changed": bool(changed), "version": stock_repo.current_version()}


class NoticeIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    center_ids: list[str] = []


@router.post("/notices", summary="發一則公告（寫進所有信箱 + 推 topic）")
async def notice(body: NoticeIn):
    count = mailbox_service.broadcast("service.notice", {"notice_id": new_id("notice"), "title": body.title,
                                                         "center_ids": body.center_ids})
    return {"mailboxes": count}


class DeviceIn(BaseModel):
    token: str | None = Field(None, description="手機的 FCM token；不給就用本機假裝置")
    mailbox_id: str | None = Field(None, description="不給就新建一個信箱")


@router.post("/devices", summary="直接登記一支手機（測試用，不用 mailbox_key）")
async def register_device(body: DeviceIn):
    mailbox_id, key = body.mailbox_id, None
    if mailbox_id is None:
        mb = mailbox_service.create()
        mailbox_id, key = mb.mailbox_id, mb.mailbox_key
    elif not mailbox_service.exists(mailbox_id):
        raise E.not_found("信箱")
    token = body.token or fcm.local_token(mailbox_id)
    devices_service.register(mailbox_id, "fcm", token)
    return {"mailbox_id": mailbox_id, "mailbox_key": key, "device_token": token}


class PushIn(BaseModel):
    type: Literal[tuple(EVENT_TYPES)] = "reservation.booked"  # type: ignore[valid-type]
    token: str | None = Field(None, description="推給這個 token")
    mailbox_id: str | None = Field(None, description="推給這個信箱所有裝置")
    all: bool = Field(False, description="推給 DB 裡所有裝置")
    topic: bool = Field(False, description="service.notice 推到 topic")
    reservation_id: str | None = "B202611070001"
    variant_id: str | None = None
    center_id: Literal["heyi", "south", "west"] = "heyi"
    deadline: str | None = None
    title: str | None = Field(None, description="公告標題（service.notice）")


@router.post("/push", summary="不改任何狀態，直接推一則通知")
async def push(body: PushIn):
    if body.topic:
        return {"results": [await notification_service.send_topic(body.title or "測試公告")]}
    if body.token:
        targets = [(body.token, body.mailbox_id)]
    elif body.mailbox_id:
        targets = [(d.token, d.mailbox_id) for d in devices_repo.by_mailbox(body.mailbox_id)]
    elif body.all:
        targets = [(d.token, d.mailbox_id) for d in devices_repo.all_devices()]
    else:
        raise E.invalid_field(["token|mailbox_id|all|topic"])
    if not targets:
        raise E.not_found("裝置")
    results = await notification_service.send_direct(
        targets, body.type, reservation_id=body.reservation_id if body.type.startswith("reservation.") else None,
        variant_id=body.variant_id or ("181" if body.type == "stock.arrived" else None),
        deadline=body.deadline or (today() + timedelta(days=1)).isoformat(), center_id=body.center_id,
        notice_title=body.title)
    return {"results": results}


@router.get("/events", summary="某信箱收到的事件（= App pull 會拿到的）")
async def events(mailbox_id: str, cursor: int = 0):
    row = mailbox_repo.get(mailbox_id)
    if row is None:
        raise E.not_found("信箱")
    return {"events": [e.model_dump(mode="json") for e in mailbox_service.events_after(row, cursor)]}
