from app.tools.crawlers.schemas import CatalogCategory


def fetch_catalog() -> list[CatalogCategory]:
    """【爬什麼】臺北市二手輔具「可以借哪些東西」的清單（類別 + 品項）。

    ─────────────────────────────────────────
    網址
        https://tpap.gov.taipei/app37/rentView/index
        （臺北市輔具資源入口網 → 二手輔具借用。網頁是伺服器直接產生的 HTML，沒有 API，
          用 requests 抓 HTML、BeautifulSoup 解析即可。先用瀏覽器打開，按 F12 看結構。）

    ─────────────────────────────────────────
    步驟
        1. 打開上面網址，頁面上會有「輔具類別」的分類（約 12 類，例如輪椅類、助行器類）。
        2. 每個類別底下有好幾種輔具（全部約 62 種），每種會有名稱、照片、規格 / 說明。
        3. 把每個類別、每種輔具都抓下來。
        4. 如果一個類別要點進去才看得到品項，就逐一請求每個類別的頁面。

    ─────────────────────────────────────────
    網頁上看到的 → 要填的欄位

        類別（CatalogCategory）
        | 網頁上的東西                          | 欄位         | 範例      |
        |---------------------------------------|--------------|-----------|
        | 類別的代碼（option value / 網址參數）  | category_id  | "1"       |
        | 類別名稱文字                          | name         | "輪椅類"  |
        | 這個類別底下的所有品項                | variants     | [...]     |

        品項（CatalogVariant）
        | 網頁上的東西                          | 欄位         | 範例                                  |
        |---------------------------------------|--------------|---------------------------------------|
        | 品項的代碼（按鈕 / 連結 / input 的值） | variant_id   | "101"                                 |
        | 所屬類別的代碼                        | category_id  | "1"                                   |
        | 品項名稱                              | name         | "一般型輪椅"                          |
        | 照片 <img src>（轉成完整網址）         | photo_url    | "https://tpap.gov.taipei/.../101.jpg" |
        | 規格文字（尺寸、重量…），沒有填 None   | spec         | "座寬 45cm"                           |
        | 說明 / 注意事項，沒有填 None           | description  | "適合短距離移動"                      |

    ─────────────────────────────────────────
    注意
        - variant_id / category_id 一定要用「官網自己的代碼」，不要自己編號或用名稱。
          每次爬都要一樣，而且要跟 fetch_stock() 的 variant_id 對得上。
        - 照片網址如果是相對路徑（/app37/img/...），前面補上 https://tpap.gov.taipei
        - 文字去掉前後空白和換行。

    ─────────────────────────────────────────
    回傳範例
        [
            {
                "category_id": "1",
                "name": "輪椅類",
                "variants": [
                    {"variant_id": "101", "category_id": "1", "name": "一般型輪椅",
                     "photo_url": "https://tpap.gov.taipei/.../101.jpg",
                     "spec": "座寬 45cm", "description": "適合短距離移動"}
                ]
            }
        ]

    檢查：python -m app.tools.crawlers.check catalog
    後端快取 1 小時，很少呼叫。
    """
    raise NotImplementedError("fetch_catalog 尚未實作")
