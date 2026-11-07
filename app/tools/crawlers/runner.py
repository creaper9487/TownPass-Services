"""後端呼叫爬蟲的共用入口：放到 thread 執行，並用 schemas 驗證回傳格式。

TEST_MODE=true 時不呼叫真的爬蟲，改用 app/tools/testdata.py 的固定假資料（同樣經過格式驗證）。
"""

import asyncio
from typing import Any, Callable, TypeVar

from pydantic import TypeAdapter

from app.config import get_settings

T = TypeVar("T")


async def run_crawler(fn: Callable[..., Any], result_type: type[T], *args: Any) -> T:
    if get_settings().test_mode:
        from app.tools.testdata import FAKES

        fn = FAKES.get(getattr(fn, "__name__", ""), fn)
    raw = await asyncio.to_thread(fn, *args)
    return TypeAdapter(result_type).validate_python(raw, from_attributes=True)
