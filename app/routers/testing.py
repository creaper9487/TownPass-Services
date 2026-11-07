"""測試模式專用 API（/_test/*）。TEST_MODE=false 時全部回 404。

用來在不需要中心系統、不需要等時間的情況下，直接觸發各種狀態與推播：
    GET  /_test/state                          目前狀態總覽（信箱、預約、裝置、最近推播）
    POST /_test/scenario                       一鍵：建信箱 + 登記裝置 + 借用預約（會推「預約成功」）
    POST /_test/reservations/{id}/trigger      讓預約進入某個狀態（會推對應通知）
    POST /_test/stock                          設定某款庫存（0 → >0 會推「到貨通知」）
    POST /_test/notices                        發一則公告（推「服務公告」）
CLI（python -m app.cli）就是在打這些 API。
"""

import json
from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.config import get_settings
from app.features.devices import repository as devices_repo
from app.features.devices import service as devices_service
from app.features.mailbox import repository as mailbox_repo
from app.features.mailbox import service as mailbox_service
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
    if not get_settings().test_mode:
        raise HTTPException(status_code=404)


router = APIRouter(prefix="/_test", tags=["test mode"], dependencies=[Depends(require_test_mode)])

TEST_CONTACT = {"name": "測試使用者", "mobile": "0900000000", "gender": "X"}


@router.get("/state", summary="狀態總覽")
async def state(limit: int = 20):
    return {
        "test_mode": True,
        "fcm_enabled": fcm.is_enabled(),
        "stock_version": stock_repo.current_version(),
        "mailboxes": [{"mailbox_id": m.id, "events": len(m.events), "next_cursor": m.next_cursor,
                       "devices": len(devices_repo.by_mailbox(m.id))} for m in mailbox_repo.mailboxes.values()],
        "reservations": [{"id": r.id, "service": r.service, "status": r.status, "center_id": r.center_id,
                          "mailbox_id": r.mailbox_id, "items": r.items, "pickup_deadline": r.pickup_deadline,
                          "forward_state": r.forward_state} for r in reservation_repo.reservations.values()],
        "devices": [{"token": d.token[:12] + "…", "mailbox_id": d.mailbox_id, "updated_at": d.updated_at}
                    for d in devices_repo.all_devices()],
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
    variant_id = body.variant_id or next((r.variant_id for r in stock_repo.rows.values() if r.stock > 0), None)
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
    row = reservation_repo.reservations.get(reservation_id)
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
            await reservation_service.expire_overdue()
        case _:
            await reservation_service.apply_center_status(row.id, body.event)
    return {"id": row.id, "status": row.status, "version": row.version}


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
