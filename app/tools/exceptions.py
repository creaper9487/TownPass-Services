"""錯誤處理：統一回傳 RFC 9457 application/problem+json。

格式：{"type": "about:blank", "title": ..., "status": 409, "code": "OUT_OF_STOCK", ...額外欄位}

在 service 裡直接 raise AppError("OUT_OF_STOCK", 409, "...", stock=0, waiting=3) 即可。
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.tools.logger import get_logger

logger = get_logger(__name__)

PROBLEM_JSON = "application/problem+json"


class AppError(Exception):
    def __init__(self, code: str, status: int, title: str, **extra):
        super().__init__(title)
        self.code = code
        self.status = status
        self.title = title
        self.extra = extra


# 規格錯誤碼
def out_of_stock(stock: int, waiting: int) -> AppError:
    return AppError("OUT_OF_STOCK", 409, "該品項已無庫存", stock=stock, waiting=waiting)


def duplicate_waitlist() -> AppError:
    return AppError("DUPLICATE_WAITLIST", 409, "同類別已有到貨通知")


def pickup_window_closed() -> AppError:
    return AppError("PICKUP_WINDOW_CLOSED", 422, "所選中心在取貨期限內沒有開館日")


def invalid_field(fields: list[str]) -> AppError:
    return AppError("INVALID_FIELD", 422, "欄位格式錯誤", fields=fields)


def not_eligible() -> AppError:
    return AppError("NOT_ELIGIBLE", 422, "居住地不在服務範圍（只服務臺北市）")


def bad_key() -> AppError:
    return AppError("BAD_KEY", 401, "金鑰不符")


def idempotency_conflict() -> AppError:
    return AppError("IDEMPOTENCY_CONFLICT", 409, "同一 Idempotency-Key 送了不同內容")


def rate_limited() -> AppError:
    return AppError("RATE_LIMITED", 429, "請求過於頻繁")


def not_found(what: str = "資源") -> AppError:
    return AppError("NOT_FOUND", 404, f"找不到{what}")


def _problem(status: int, code: str, title: str, **extra) -> JSONResponse:
    body = {"type": "about:blank", "title": title, "status": status, "code": code, **extra}
    return JSONResponse(status_code=status, content=body, media_type=PROBLEM_JSON)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError):
        return _problem(exc.status, exc.code, exc.title, **exc.extra)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError):
        # 只列欄位名，不回顯使用者輸入的值（可能是個資）
        fields = sorted({".".join(str(p) for p in e["loc"][1:]) or str(e["loc"][0]) for e in exc.errors()})
        return _problem(422, "INVALID_FIELD", "欄位格式錯誤", fields=fields)

    @app.exception_handler(NotImplementedError)
    async def _not_implemented(_: Request, exc: NotImplementedError):
        # 爬蟲 / 外部介接還沒寫好時會走到這裡
        return _problem(501, "NOT_IMPLEMENTED", str(exc) or "尚未實作")

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception):
        # 不記錄 request body，避免個資進日誌
        logger.error("Unhandled error: %s", type(exc).__name__)
        return _problem(500, "INTERNAL", "Internal server error")
