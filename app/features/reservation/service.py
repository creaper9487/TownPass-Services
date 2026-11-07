"""預約：建立、取消、批次查詢、逾期自動取消、取貨提醒、中心回寫狀態。

- 預約記錄在本機 SQLite（不含聯絡資料）。
- 欄位規則、服務、可選項目都讀 app/config.py（validate_against_config），不寫死。
- config.FORWARD_TO_CENTER = False 時不送到中心，forward_state = "off"。
"""

import hashlib
import json
import secrets
from datetime import datetime, timedelta

from app import config
from app.features.catalog import service as catalog_service
from app.features.centers import service as centers_service
from app.features.forwarding import service as forwarding_service
from app.features.mailbox import service as mailbox_service
from app.features.reservation import repository as repo
from app.features.reservation.schemas import (
    BatchGetError,
    BatchGetItem,
    CancelResult,
    FormOut,
    PickupInfo,
    ReservationCreate,
    ReservationCreated,
    ReservationStatus,
)
from app.features.stock import service as stock_service
from app.tools import exceptions as E
from app.tools.districts import DISTRICT_TO_CENTER
from app.tools.fields import required_fields
from app.tools.security import hash_secret, new_secret, verify_secret
from app.tools.timeutil import TAIPEI as TZ, now, today

TAIPEI = {"臺北市", "台北市"}
FINAL_STATUSES = {"completed", "cancelled", "expired"}
_PREFIX = {"borrow": "B", "assess": "A", "repair": "R", "recycle": "C"}
OTHER = "其他"


# ---------- 依 config 驗證 ----------
def form(service: str) -> FormOut:
    """GET /forms/{service}：表單選項與必填欄位，全部來自 config。"""
    svc = config.SERVICES.get(service)
    if svc is None or not svc["enabled"]:
        raise E.not_found("服務")
    groups = svc["groups"]
    return FormOut(
        service=service, label=svc["label"],
        item_options=(svc["item_options"] or []) + ([OTHER] if svc["allow_other"] else []),
        allow_other=svc["allow_other"], max_items=svc["max_items"], required_fields=required_fields(service),
        districts=config.TAIPEI_DISTRICTS,
        fields={n: r for n, r in config.FIELDS.items() if n.split(".")[0] in groups or n == "other_text"},
    )


async def validate_against_config(p: ReservationCreate) -> None:
    """服務是否開放、該填的欄位組、items 是否合法（借用：品項存在且開放；其他：在可選項目內）。"""
    svc = config.SERVICES.get(p.service)
    if svc is None or not svc["enabled"]:
        raise E.invalid_field(["service"])
    missing = [g for g in ("subject", "pickup") if g in svc["groups"] and getattr(p, g) is None]
    if p.service == "borrow" and p.center_id is None:
        missing.append("center_id")
    if missing:
        raise E.invalid_field(missing)

    if len(p.items) > svc["max_items"] or len(set(p.items)) != len(p.items):
        raise E.invalid_field(["items"])
    if svc["item_options"] is None:  # 借用：items 是品項代碼
        for vid in p.items:
            await catalog_service.check_variant(vid, field="items")
    else:
        allowed = set(svc["item_options"]) | ({OTHER} if svc["allow_other"] else set())
        if any(i not in allowed for i in p.items):
            raise E.invalid_field(["items"])
        if OTHER in p.items and not p.other_text:
            raise E.invalid_field(["other_text"])


# ---------- helpers ----------
def _pickup(row: repo.ReservationRow) -> PickupInfo | None:
    if row.pickup_deadline is None:
        return None
    return PickupInfo(deadline=row.pickup_deadline, open_dates=row.pickup_dates)


def _status(row: repo.ReservationRow) -> ReservationStatus:
    return ReservationStatus(id=row.id, status=row.status, version=row.version,
                             updated_at=row.updated_at, pickup=_pickup(row))


def _created(row: repo.ReservationRow, access_key: str) -> ReservationCreated:
    return ReservationCreated(id=row.id, access_key=access_key, status=row.status, pickup=_pickup(row))


def _new_reservation_id(service: str) -> str:
    while True:
        rid = f"{_PREFIX[service]}{today():%Y%m%d}{secrets.randbelow(10000):04d}"
        if not repo.exists(rid):
            return rid


def _resolve_center(p: ReservationCreate) -> str:
    """借用用使用者選的中心；其他服務依居住行政區分派，算完即丟棄行政區。只服務臺北市。"""
    if p.service == "borrow":
        return p.center_id
    if p.service in ("assess", "repair"):
        if p.subject.living_county not in TAIPEI:
            raise E.not_eligible()
        district = p.subject.living_district
    else:
        district = p.pickup.district
    if district not in DISTRICT_TO_CENTER:
        raise E.not_eligible()
    return DISTRICT_TO_CENTER[district]


def _set_status(row: repo.ReservationRow, status: str) -> None:
    row.status = status
    row.version += 1
    row.updated_at = now()
    repo.save(row)


def _load(reservation_id: str, access_key: str) -> repo.ReservationRow:
    row = repo.get(reservation_id)
    if row is None or not verify_secret(access_key, row.access_key_hash):
        raise E.bad_key()
    return row


# ---------- API ----------
async def create(p: ReservationCreate, idempotency_key: str) -> ReservationCreated:
    body_hash = hashlib.sha256(json.dumps(p.model_dump(mode="json"), sort_keys=True).encode()).hexdigest()
    saved = repo.get_idempotency(idempotency_key)
    if saved:
        saved_hash, rid, key = saved
        if saved_hash != body_hash:
            raise E.idempotency_conflict()
        return _created(repo.get(rid), key)

    if not mailbox_service.exists(p.mailbox_id):
        raise E.invalid_field(["mailbox_id"])
    await validate_against_config(p)

    center_id = _resolve_center(p)
    deadline, open_dates = None, []
    if p.service == "borrow":
        deadline, open_dates = await centers_service.pickup_window(center_id, today())
        stock_service.reserve(p.items)  # 不夠會 raise OUT_OF_STOCK，什麼都不扣

    access_key = new_secret()
    t = now()
    row = repo.ReservationRow(
        id=_new_reservation_id(p.service), access_key_hash=hash_secret(access_key), mailbox_id=p.mailbox_id,
        service=p.service, center_id=center_id, items=list(p.items),
        status="booked" if p.service == "borrow" else "submitted", version=1,
        pickup_deadline=deadline, pickup_dates=open_dates,
        forward_state="pending" if config.FORWARD_TO_CENTER else "off", created_at=t, updated_at=t,
    )
    repo.insert(row)
    repo.put_idempotency(idempotency_key, body_hash, row.id, access_key, t.isoformat())

    if config.FORWARD_TO_CENTER:  # 個資只進送件佇列（記憶體），不進資料庫
        forwarding_service.enqueue(row.id, {"reservation_id": row.id, **p.model_dump(mode="json"),
                                            "center_id": center_id})

    if p.service == "borrow":
        mailbox_service.append_event(
            row.mailbox_id, "reservation.booked", ref={"reservation_id": row.id},
            data={"pickup_deadline": deadline.isoformat(), "pickup_dates": [d.isoformat() for d in open_dates]},
        )
    return _created(row, access_key)


async def cancel(reservation_id: str, access_key: str) -> CancelResult:
    """使用者取消；重複呼叫結果相同。"""
    row = _load(reservation_id, access_key)
    await _cancel_row(row)
    return CancelResult(id=row.id, status=row.status, version=row.version)


async def _cancel_row(row: repo.ReservationRow) -> None:
    if row.status in FINAL_STATUSES:
        return
    if row.service == "borrow":
        await stock_service.release(row.items)
    forwarding_service.cancel(row.id)
    _set_status(row, "cancelled")
    mailbox_service.append_event(row.mailbox_id, "reservation.cancelled", ref={"reservation_id": row.id})


def batch_get(items: list[BatchGetItem]) -> list[ReservationStatus | BatchGetError]:
    """密鑰不符或不存在都回 {id, error: "BAD_KEY"}，不透露該 id 是否存在。"""
    out: list[ReservationStatus | BatchGetError] = []
    for it in items:
        row = repo.get(it.id)
        if row and verify_secret(it.access_key, row.access_key_hash):
            out.append(_status(row))
        else:
            out.append(BatchGetError(id=it.id))
    return out


def set_forward_state(reservation_id: str, state: str) -> None:
    row = repo.get(reservation_id)
    if row:
        row.forward_state = state
        repo.save(row)


async def apply_center_status(reservation_id: str, status: str) -> bool:
    """中心 webhook / 測試工具：confirmed / completed / cancelled。"""
    row = repo.get(reservation_id)
    if row is None:
        return False
    if row.status in FINAL_STATUSES or row.status == status:
        return True
    if status == "cancelled":
        await _cancel_row(row)
        return True
    _set_status(row, status)
    mailbox_service.append_event(row.mailbox_id, f"reservation.{status}", ref={"reservation_id": row.id})
    return True


# ---------- 背景工作 ----------
async def expire_overdue() -> int:
    """借用逾期未取貨：自動取消、釋回庫存、寫 reservation.expired。"""
    t = now()
    count = 0
    for row in repo.booked_borrows():
        if row.pickup_deadline is None:
            continue
        end_of_deadline = datetime.combine(row.pickup_deadline + timedelta(days=1), datetime.min.time(), TZ)
        if t >= end_of_deadline:
            await stock_service.release(row.items)
            forwarding_service.cancel(row.id)
            _set_status(row, "expired")
            mailbox_service.append_event(row.mailbox_id, "reservation.expired", ref={"reservation_id": row.id})
            count += 1
    return count


async def send_pickup_reminders() -> None:
    """取貨期限當天：開館時提醒一次、閉館前 2 小時再提醒一次。"""
    t = now()
    for row in repo.booked_borrows():
        if row.pickup_deadline != t.date():
            continue
        try:
            day = (await centers_service.get_calendar(row.center_id, t.date(), 1))[0]
        except NotImplementedError:
            return
        if not day.open or not day.hours:
            continue
        opening = datetime.combine(t.date(), datetime.strptime(day.hours[0].from_, "%H:%M").time(), TZ)
        closing = datetime.combine(t.date(), datetime.strptime(day.hours[-1].to, "%H:%M").time(), TZ)
        for tag, at in (("open", opening), ("close-2h", closing - timedelta(hours=2))):
            if tag not in row.reminders_sent and at <= t < closing:
                row.reminders_sent.add(tag)
                repo.save(row)
                mailbox_service.append_event(
                    row.mailbox_id, "reservation.pickup_reminder", ref={"reservation_id": row.id},
                    data={"pickup_deadline": row.pickup_deadline.isoformat()},
                )
                break  # 一次只送一則
