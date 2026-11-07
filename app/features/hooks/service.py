"""入站 webhook（中心 → 我們）：驗 HMAC 簽章、以 event_id 去重、分派到對應 feature。"""

from app import config
from app.config import get_settings
from app.features.hooks.schemas import CenterStatusHook, CenterStockHook
from app.features.reservation import service as reservation_service
from app.features.stock import service as stock_service
from app.tools import exceptions as E
from app.tools.crawlers.schemas import StockItem
from app.tools.security import verify_signature

_seen_event_ids: set[str] = set()  # TODO: 正式版放資料庫並設保存期限


def verify(body: bytes, timestamp: str | None, signature: str | None) -> None:
    s = get_settings()
    if not verify_signature(s.hook_secret, timestamp or "", body, signature or "", config.HOOK_MAX_SKEW_SECONDS):
        raise E.AppError("BAD_SIGNATURE", 401, "簽章驗證失敗")


def _first_time(event_id: str) -> bool:
    if event_id in _seen_event_ids:
        return False
    _seen_event_ids.add(event_id)
    return True


async def handle_status(hook: CenterStatusHook) -> None:
    if not _first_time(hook.event_id):
        return
    if not await reservation_service.apply_center_status(hook.reservation_id, hook.status):
        _seen_event_ids.discard(hook.event_id)
        raise E.not_found("預約")


async def handle_stock(hook: CenterStockHook) -> None:
    if not _first_time(hook.event_id):
        return
    await stock_service.apply_items([StockItem(variant_id=hook.variant_id, stock=hook.stock, waiting=hook.waiting)])


def reset() -> None:
    _seen_event_ids.clear()
