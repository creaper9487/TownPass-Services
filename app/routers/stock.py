from fastapi import APIRouter, Query, Request

from app.features.stock import service
from app.routers.deps import etag_json

router = APIRouter(tags=["stock"])


@router.get("/stock", summary="全部庫存；?since={version} 只回有變動的品項")
async def get_stock(request: Request, since: int | None = Query(None, ge=0)):
    data = service.snapshot(since)
    etag = f'"{data["version"]}"'
    return etag_json(request, data, etag, max_age=0)
