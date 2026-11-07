"""集中註冊所有 router。新增 router 時在這裡 include 即可。"""

from fastapi import APIRouter

from app.routers import example, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(example.router)
