"""入站 webhook：中心 → 我們。Header 需帶 X-Timestamp（unix 秒）與 X-Signature（HMAC-SHA256）。"""

from fastapi import APIRouter, Header, Request, Response

from app.features.hooks import service
from app.features.hooks.schemas import CenterStatusHook, CenterStockHook
from app.tools import exceptions as E

router = APIRouter(prefix="/hooks/center", tags=["hooks"])


async def _verified_body(request: Request, ts: str | None, sig: str | None) -> bytes:
    body = await request.body()
    service.verify(body, ts, sig)
    return body


@router.post("/status", status_code=204, summary="中心回寫預約狀態")
async def center_status(request: Request, x_timestamp: str | None = Header(None), x_signature: str | None = Header(None)):
    body = await _verified_body(request, x_timestamp, x_signature)
    try:
        hook = CenterStatusHook.model_validate_json(body)
    except ValueError:
        raise E.invalid_field(["body"]) from None
    await service.handle_status(hook)
    return Response(status_code=204)


@router.post("/stock", status_code=204, summary="中心推送庫存")
async def center_stock(request: Request, x_timestamp: str | None = Header(None), x_signature: str | None = Header(None)):
    body = await _verified_body(request, x_timestamp, x_signature)
    try:
        hook = CenterStockHook.model_validate_json(body)
    except ValueError:
        raise E.invalid_field(["body"]) from None
    await service.handle_stock(hook)
    return Response(status_code=204)
