"""範例 router：只負責 HTTP 層（參數、回應格式），商業邏輯交給 features。"""

from fastapi import APIRouter

from app.features.example import service
from app.features.example.schemas import ItemCreate, ItemOut
from app.tools.response import ApiResponse, ok

router = APIRouter(prefix="/examples", tags=["example"])


@router.get("", response_model=ApiResponse[list[ItemOut]])
async def list_items():
    return ok(service.list_items())


@router.get("/{item_id}", response_model=ApiResponse[ItemOut])
async def get_item(item_id: int):
    return ok(service.get_item(item_id))


@router.post("", response_model=ApiResponse[ItemOut], status_code=201)
async def create_item(payload: ItemCreate):
    return ok(service.create_item(payload))
