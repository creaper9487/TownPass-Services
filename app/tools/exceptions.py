"""自訂例外與全域 exception handler。

在 service 中直接 raise AppError 子類別，會自動轉成統一格式的錯誤回應。
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.tools.logger import get_logger
from app.tools.response import fail

logger = get_logger(__name__)


class AppError(Exception):
    status_code = 400

    def __init__(self, message: str = "Bad request"):
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = 404


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error_handler(_: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content=fail(exc.message))

    @app.exception_handler(Exception)
    async def _unhandled_handler(_: Request, exc: Exception):
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(status_code=500, content=fail("Internal server error"))
