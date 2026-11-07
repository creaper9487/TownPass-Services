"""集中註冊所有 router。新增 router 時在這裡 include 即可。

分層：routers 只處理 HTTP（參數、header、狀態碼、ETag），邏輯都在 features/*/service.py。
"""

from fastapi import APIRouter

from app.routers import catalog, centers, health, hooks, mailboxes, reservations, stock, subscriptions

api_router = APIRouter()
for r in (health, catalog, centers, stock, mailboxes, reservations, subscriptions, hooks):
    api_router.include_router(r.router)
