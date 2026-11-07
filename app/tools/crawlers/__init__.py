"""爬蟲 / 外部資料來源。給爬蟲組實作。

規則：
1. 每個 function 都是「同步」function，可以直接用 requests / httpx / BeautifulSoup。
   後端會用 asyncio.to_thread 呼叫，不會卡住 server。
2. 回傳值必須符合 schemas.py 裡的格式（回傳 Pydantic model 或同欄位的 dict 都可以），
   後端會用 schemas.py 驗證，格式不對會直接報錯。
3. 還沒寫好的 function 保持 raise NotImplementedError，API 會回 501。
4. 不要在爬蟲裡 print / log 任何個資。

| function                         | 檔案               | 被誰用                         |
|----------------------------------|--------------------|-------------------------------|
| fetch_catalog()                  | catalog.py         | GET /catalog                  |
| fetch_stock()                    | stock.py           | 背景每 30–60 秒同步 → GET /stock |
| fetch_centers()                  | centers.py         | GET /centers                  |
| fetch_center_calendar(...)       | center_calendar.py | GET /centers/{id}/calendar、計算取貨期限 |
| forward_reservation(...)         | center_forward.py  | 送件佇列 → 輔具中心            |
"""

from app.tools.crawlers.center_calendar import fetch_center_calendar
from app.tools.crawlers.catalog import fetch_catalog
from app.tools.crawlers.center_forward import forward_reservation
from app.tools.crawlers.centers import fetch_centers
from app.tools.crawlers.stock import fetch_stock

__all__ = [
    "fetch_catalog",
    "fetch_stock",
    "fetch_centers",
    "fetch_center_calendar",
    "forward_reservation",
]
