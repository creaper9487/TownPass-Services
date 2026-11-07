"""後端呼叫爬蟲的共用入口：放到 thread 執行，並用 schemas 驗證回傳格式。

- TEST_MODE=true 時不呼叫真的爬蟲，改用 app/tools/testdata.py 的固定假資料（同樣經過格式驗證）。
- 爬蟲失敗（官網連不到、改版、格式不對）→ 503 SOURCE_UNAVAILABLE，不會變成看不懂的 500。
  還沒寫好的爬蟲（NotImplementedError）照舊往上丟（API 回 501）。
"""

import asyncio
from typing import Any, Callable, TypeVar

from pydantic import TypeAdapter

from app.config import get_settings
from app.tools import exceptions as E
from app.tools.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


async def run_crawler(fn: Callable[..., Any], result_type: type[T], *args: Any) -> T:
    name = getattr(fn, "__name__", "crawler")
    if get_settings().test_mode:
        from app.tools.testdata import FAKES

        fn = FAKES.get(name, fn)
    try:
        raw = await asyncio.to_thread(fn, *args)
        return TypeAdapter(result_type).validate_python(raw, from_attributes=True)
    except (NotImplementedError, E.AppError):
        raise
    except Exception as exc:  # noqa: BLE001
        logger.warning("%s failed: %s", name, type(exc).__name__)
        raise E.source_unavailable() from exc
