"""後端呼叫爬蟲的共用入口：放到 thread 執行，並用 schemas 驗證回傳格式。"""

import asyncio
from typing import Any, Callable, TypeVar

from pydantic import TypeAdapter

T = TypeVar("T")


async def run_crawler(fn: Callable[..., Any], result_type: type[T], *args: Any) -> T:
    raw = await asyncio.to_thread(fn, *args)
    return TypeAdapter(result_type).validate_python(raw, from_attributes=True)
