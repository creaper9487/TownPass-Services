from app.tools.crawlers.schemas import CatalogCategory


def fetch_catalog() -> list[CatalogCategory]:
    """【爬什麼】臺北市二手輔具「可以借哪些東西」的目錄（分類 + 款式）。

    ─────────────────────────────────────────
    網址
        https://tpap.gov.taipei/app37/rentView/index
        （臺北市輔具資源入口網 → 二手輔具借用。網頁是伺服器直接產生的 HTML，沒有 API，
          用 requests 抓 HTML、BeautifulSoup 解析即可。先用瀏覽器打開，按 F12 看結構。）

    ─────────────────────────────────────────
    步驟
        1. 打開網址，找到「輔具分類」（約 12 類，例：輪椅類、助行器類）。
        2. 每個分類底下有好幾款輔具（全部約 62 款），每款有名稱、照片、規格、說明。
        3. 全部分類、全部款式都抓下來。分類要點進去才看得到款式，就逐一請求每個分類頁。
        4. 規格裡如果有「適用身高」「座寬」「承重」，額外轉成數字填到 attrs。

    ─────────────────────────────────────────
    網頁上看到的 → 要填的欄位

        分類（CatalogCategory）
        | 網頁上的東西                          | 欄位      | 範例                                |
        |---------------------------------------|-----------|-------------------------------------|
        | 分類代碼（option value / 網址參數）    | id        | "1"                                 |
        | 分類名稱                              | name      | "輪椅類"                            |
        | 分類的代表圖（沒有填 None）            | image     | "https://tpap.gov.taipei/.../c1.jpg" |
        | 這個分類底下的所有款式                | variants  | [...]                               |

        款式（CatalogVariant）
        | 網頁上的東西                          | 欄位         | 範例                                    |
        |---------------------------------------|--------------|-----------------------------------------|
        | 款式代碼（按鈕 / 連結 / input 的值）   | id           | "101"                                   |
        | 款式名稱                              | name         | "一般型輪椅"                            |
        | 照片 <img src>（轉成完整網址）         | image        | "https://tpap.gov.taipei/.../101.jpg"   |
        | 規格，一行拆成一筆                    | specs        | ["座寬 18 吋", "重量 15 公斤"]          |
        | 說明 / 注意事項（沒有填 None）         | description  | "適合短距離移動"                        |
        | 規格裡的數字（見下表，沒有就 None）    | attrs        | {"seat_width_in": 18, ...}              |

        attrs（只填規格裡真的有寫的，其他 None；整個都沒有就 attrs=None）
        | 規格上寫的        | 欄位           | 單位 | 範例                       |
        |-------------------|----------------|------|----------------------------|
        | 適用身高 150–180  | height_min     | 公分 | 150                        |
        |                   | height_max     | 公分 | 180                        |
        | 座寬 18 吋        | seat_width_in  | 英吋 | 18（寫公分要 ÷ 2.54 換算） |
        | 承重 100 公斤     | weight_max_kg  | 公斤 | 100                        |

    ─────────────────────────────────────────
    注意
        - 分類 id、款式 id 一定要用「官網自己的代碼」，不要自己編號、不要用名稱。
          每次爬都要一樣，而且款式 id 要跟 fetch_stock() 的 variant_id 對得上。
        - 圖片網址是相對路徑（/app37/img/...）的話，前面補 https://tpap.gov.taipei
        - 文字去掉前後空白和換行。

    ─────────────────────────────────────────
    回傳範例
        [
            {
                "id": "1",
                "name": "輪椅類",
                "image": "https://tpap.gov.taipei/.../c1.jpg",
                "variants": [
                    {
                        "id": "101",
                        "name": "一般型輪椅",
                        "image": "https://tpap.gov.taipei/.../101.jpg",
                        "specs": ["座寬 18 吋", "重量 15 公斤"],
                        "description": "適合短距離移動",
                        "attrs": {"height_min": null, "height_max": null,
                                  "seat_width_in": 18, "weight_max_kg": 100}
                    }
                ]
            }
        ]

    檢查：python -m app.tools.crawlers.check catalog
    後端快取 1 小時，很少呼叫。
    """
    raise NotImplementedError("fetch_catalog 尚未實作")
