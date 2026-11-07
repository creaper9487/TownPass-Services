from app.tools.crawlers.schemas import CatalogCategory


def fetch_catalog() -> list[CatalogCategory]:
    """抓取「二手輔具借用」的全部品項目錄。

    資料來源：
        https://tpap.gov.taipei/app37/rentView/index
        （臺北市輔具資源入口網．二手輔具借用；伺服器端渲染 HTML，沒有公開 API）

    需要的功能：
        1. 抓出所有「類別」（官網約 12 類，例：輪椅類、助行器類、居家照顧類…）。
        2. 每個類別底下的「品項」（共約 62 種），每個品項要有：
           名稱、照片網址、規格、說明。
        3. variant_id / category_id 用官網原始代碼，必須每次爬都一樣。
        4. 照片網址要轉成絕對網址（https://tpap.gov.taipei/...）。

    回傳：
        list[CatalogCategory]，範例：
        [
            {
                "category_id": "1",
                "name": "輪椅類",
                "variants": [
                    {
                        "variant_id": "101",
                        "category_id": "1",
                        "name": "一般型輪椅",
                        "photo_url": "https://tpap.gov.taipei/.../101.jpg",
                        "spec": "座寬 45cm",
                        "description": "適合短距離移動"
                    }
                ]
            }
        ]

    呼叫頻率：後端快取 1 小時，很少呼叫。
    """
    raise NotImplementedError("fetch_catalog 尚未實作")
