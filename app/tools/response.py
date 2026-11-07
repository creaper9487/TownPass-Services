"""統一的 API 回應格式：{"success": bool, "data": ..., "message": str | None}"""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    message: str | None = None


def ok(data=None, message: str | None = None) -> dict:
    return {"success": True, "data": data, "message": message}


def fail(message: str) -> dict:
    return {"success": False, "data": None, "message": message}
