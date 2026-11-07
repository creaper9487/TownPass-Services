from datetime import date

from fastapi import APIRouter, Query, Request

from app.features.centers import service
from app.routers.deps import etag_json
from app.tools.cache import etag_of
from app.tools.timeutil import today

router = APIRouter(prefix="/centers", tags=["centers"])


@router.get("", summary="3 間中心（ETag；max-age 3600）")
async def list_centers(request: Request):
    data, etag = await service.get_centers()
    return etag_json(request, {"centers": data}, etag, max_age=3600)


@router.get("/{center_id}/calendar", summary="逐日是否開館（ETag；max-age 300）")
async def get_calendar(
    request: Request,
    center_id: str,
    from_: date | None = Query(None, alias="from"),
    days: int = Query(14, ge=1, le=60),
):
    start = from_ or today()
    days_list = await service.get_calendar(center_id, start, days)
    data = {"center_id": center_id, "days": [d.model_dump(mode="json", by_alias=True) for d in days_list]}
    return etag_json(request, data, etag_of(data), max_age=300)
