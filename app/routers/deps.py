"""router 共用：Bearer 金鑰、ETag / 304。"""

from typing import Any

from fastapi import Header, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def bearer_key(authorization: str | None = Header(None)) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return None


def etag_json(request: Request, data: Any, etag: str, max_age: int) -> Response:
    """If-None-Match 命中回 304，否則回 JSON 並帶 ETag / Cache-Control。"""
    headers = {"ETag": etag, "Cache-Control": f"max-age={max_age}"}
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers=headers)
    return JSONResponse(jsonable_encoder(data), headers=headers)
