from fastapi import APIRouter, Request

from app.features.catalog import service
from app.routers.deps import etag_json

router = APIRouter(tags=["catalog"])


@router.get("/catalog", summary="12 類 62 種品項（ETag；max-age 3600）")
async def get_catalog(request: Request):
    data, etag = await service.get_catalog()
    return etag_json(request, {"categories": data}, etag, max_age=3600)
