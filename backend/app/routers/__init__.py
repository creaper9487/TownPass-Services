"""集中註冊所有 router。要不要開哪一組 API，改 app/config.py 的 API_ENABLED。

分層：routers 只處理 HTTP（參數、header、狀態碼、ETag），邏輯都在 features/*/service.py。
"""

from fastapi import APIRouter

from app import config
from app.routers import (catalog, centers, devices, health, hooks, mailboxes, reservations, stock, subscriptions,
                         testing)
from app.tools.logger import get_logger

logger = get_logger(__name__)

ROUTERS = {
    "health": health,
    "catalog": catalog,
    "centers": centers,
    "stock": stock,
    "mailboxes": mailboxes,
    "devices": devices,
    "reservations": reservations,
    "subscriptions": subscriptions,
    "hooks": hooks,
    "test": testing,  # 另外在每個 request 檢查 TEST_MODE（testing.require_test_mode）
}


def build_api_router() -> APIRouter:
    api_router = APIRouter()
    off = []
    for name, module in ROUTERS.items():
        if config.API_ENABLED.get(name, False):
            api_router.include_router(module.router)
            if hasattr(module, "forms_router"):
                api_router.include_router(module.forms_router)
        else:
            off.append(name)
    if off:
        logger.info("API 關閉中（config.API_ENABLED）：%s", ", ".join(off))
    return api_router
