"""推播裝置登記（Bearer mailbox_key）。"""

from fastapi import APIRouter, Depends, Response

from app.features.devices import service
from app.features.devices.schemas import DeviceRegister, DeviceUnregister
from app.features.mailbox import service as mailbox_service
from app.routers.deps import bearer_key

router = APIRouter(prefix="/devices", tags=["devices"])


@router.post("", status_code=204, summary="登記 FCM token；同一個 token 重複呼叫視為更新")
async def register(body: DeviceRegister, key: str | None = Depends(bearer_key)):
    mailbox_service.authenticate(body.mailbox_id, key)
    service.register(body.mailbox_id, body.platform, body.token)
    return Response(status_code=204)


@router.delete("", status_code=204, summary="取消登記（token 放 body，不進網址與日誌）")
async def unregister(body: DeviceUnregister, mailbox_id: str, key: str | None = Depends(bearer_key)):
    mailbox_service.authenticate(mailbox_id, key)
    service.unregister(mailbox_id, body.token)
    return Response(status_code=204)


@router.delete("/{token}", status_code=204, summary="同上，相容規格原本的寫法（建議改用 body 版）")
async def unregister_by_path(token: str, mailbox_id: str, key: str | None = Depends(bearer_key)):
    mailbox_service.authenticate(mailbox_id, key)
    service.unregister(mailbox_id, token)
    return Response(status_code=204)
