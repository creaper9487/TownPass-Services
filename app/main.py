"""應用程式進入點：建立 FastAPI app、掛上 middleware 與 routers。

啟動方式（擇一）：
    1. 直接執行這個檔案（VS Code 按 ▶ 也可以）：python app/main.py
    2. 在專案根目錄：uvicorn app.main:app --reload
"""

import sys
from pathlib import Path

# 直接執行 app/main.py 時，Python 只會看到 app/ 資料夾，
# 把專案根目錄加進 sys.path，才能 import app.xxx
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import api_router
from app.tools.exceptions import register_exception_handlers
from app.tools.http_client import close_http_client
from app.tools.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup")
    yield
    await close_http_client()
    logger.info("Application shutdown")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_prefix)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True, app_dir=str(ROOT_DIR))
