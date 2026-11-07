from fastapi import APIRouter, Body, Header

from app.features.reservation import service
from app.features.reservation.schemas import (
    AccessKeyIn,
    BatchGetError,
    BatchGetItem,
    CancelResult,
    ReservationCreate,
    ReservationCreated,
    ReservationStatus,
)
from app.tools import exceptions as E

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.post("", status_code=201, response_model=ReservationCreated, summary="建立預約（Idempotency-Key 必填）")
async def create_reservation(payload: ReservationCreate, idempotency_key: str | None = Header(None)):
    if not idempotency_key:
        raise E.invalid_field(["Idempotency-Key"])
    return await service.create(payload, idempotency_key)


@router.post(":batchGet", response_model=list[ReservationStatus | BatchGetError],
             summary="Body [{id, access_key}]；密鑰不符的項目回 {id, error: BAD_KEY}")
async def batch_get(body: list[BatchGetItem] = Body(..., max_length=50)):
    return service.batch_get(body)


@router.post("/{reservation_id}:cancel", response_model=CancelResult, summary="取消（借用會釋回庫存，可重複呼叫）")
async def cancel(reservation_id: str, body: AccessKeyIn):
    return await service.cancel(reservation_id, body.access_key)
