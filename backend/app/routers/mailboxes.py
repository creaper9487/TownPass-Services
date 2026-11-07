import asyncio
import json

from fastapi import APIRouter, Depends, Header, Query, Response
from fastapi.responses import StreamingResponse

from app.features.mailbox import service
from app.features.mailbox.schemas import AckIn, EventsPage, MailboxCreated
from app.routers.deps import bearer_key

router = APIRouter(prefix="/mailboxes", tags=["mailboxes"])

NO_STORE = {"Cache-Control": "no-store"}


@router.post("", status_code=201, response_model=MailboxCreated, summary="建立匿名信箱（key 只回一次）")
async def create_mailbox():
    return service.create()


@router.get("/{mailbox_id}/events", response_model=EventsPage, summary="long-poll 取事件")
async def get_events(
    response: Response,
    mailbox_id: str,
    cursor: int = Query(0, ge=0),
    wait: int = Query(25, ge=0, le=25),
    key: str | None = Depends(bearer_key),
):
    row = service.authenticate(mailbox_id, key)
    events = await service.wait_events(row, cursor, wait)
    response.headers.update(NO_STORE)
    return EventsPage(events=events, next_cursor=events[-1].cursor if events else cursor)


@router.get("/{mailbox_id}/stream", summary="SSE 版本，Last-Event-ID = cursor")
async def stream_events(
    mailbox_id: str,
    key: str | None = Depends(bearer_key),
    last_event_id: str | None = Header(None),
):
    row = service.authenticate(mailbox_id, key)
    cursor = int(last_event_id) if last_event_id and last_event_id.isdigit() else 0

    async def gen():
        nonlocal cursor
        while True:
            events = await service.wait_events(row, cursor, 25)
            if not events:
                yield ": keep-alive\n\n"
                continue
            for e in events:
                cursor = e.cursor
                yield f"id: {e.cursor}\nevent: {e.type}\ndata: {json.dumps(e.model_dump(mode='json'), ensure_ascii=False)}\n\n"
            await asyncio.sleep(0)

    return StreamingResponse(gen(), media_type="text/event-stream", headers=NO_STORE)


@router.post("/{mailbox_id}/ack", status_code=204, summary="標記已讀到 cursor")
async def ack(mailbox_id: str, body: AckIn, key: str | None = Depends(bearer_key)):
    row = service.authenticate(mailbox_id, key)
    service.ack(row, body.cursor)
    return Response(status_code=204)
