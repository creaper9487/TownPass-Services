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

from app import config
from app.config import get_settings
from app.features import jobs
from app.routers import build_api_router
from app.tools.exceptions import register_exception_handlers
from app.tools import db
from app.tools.http_client import close_http_client
from app.tools.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup")
    if get_settings().test_mode:
        logger.warning("⚠ TEST_MODE=true：爬蟲使用固定假資料。正式環境請關閉！")
        if config.test_api_enabled():
            s = get_settings()
            logger.warning("⚠ 測試面板：http://%s:%s%s/_test/panel", s.host, s.port, config.API_PREFIX)
    tasks = jobs.start() if get_settings().enable_background_jobs else []
    yield
    await jobs.stop(tasks)
    await close_http_client()
    db.close()
    logger.info("Application shutdown")


def create_app() -> FastAPI:
    app = FastAPI(title=config.APP_NAME, debug=config.DEBUG, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(build_api_router(), prefix=config.API_PREFIX)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    s = get_settings()
    uvicorn.run("app.main:app", host=s.host, port=s.port, reload=True, app_dir=str(ROOT_DIR))
