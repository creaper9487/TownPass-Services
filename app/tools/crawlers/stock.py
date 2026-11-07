from app.tools.crawlers.schemas import StockItem


def fetch_stock() -> list[StockItem]:
    """【爬什麼】每一款二手輔具「現在還剩幾台」和「有幾個人在排隊」。

    ─────────────────────────────────────────
    網址
        https://tpap.gov.taipei/app37/rentView/index
        （跟 fetch_catalog 同一個頁面；每款輔具旁邊會顯示剩餘數量和等待人數。
          2026-11-07 看到的樣子：輪椅全部剩 0 台，等待 6～23 人。）

    ─────────────────────────────────────────
    步驟
        1. 打開網址，找到每款輔具旁邊的「剩餘數量」和「等待人數」。
        2. 每款抓一筆，全部款式都要回傳（沒變的也要，後端自己比對差異）。
        3. 只抓數字，不要下載照片、不要點進詳細頁（這個 function 每 45 秒跑一次，要快）。

    ─────────────────────────────────────────
    網頁上看到的 → 要填的欄位
        | 網頁上的東西                          | 欄位        | 型別 | 範例  |
        |---------------------------------------|-------------|------|-------|
        | 款式代碼（= fetch_catalog 款式的 id）  | variant_id  | str  | "101" |
        | 剩餘數量 / 可借數量                   | stock       | int  | 0     |
        | 等待人數 / 候補人數                   | waiting     | int  | 23    |

    ─────────────────────────────────────────
    注意
        - variant_id 必須跟 fetch_catalog() 款式的 id 一模一樣，不然前端對不上。
        - 網頁顯示「無」「-」或空白 → 當 0。
        - 數字要轉成 int，不要回傳字串 "3"。
        - 正式上線前要先取得輔具中心同意這個抓取頻率。

    ─────────────────────────────────────────
    回傳範例
        [
            {"variant_id": "101", "stock": 0, "waiting": 23},
            {"variant_id": "205", "stock": 4, "waiting": 0}
        ]

    檢查：python -m app.tools.crawlers.check stock
    """
    # ── 範本（CSS 選擇器是假的，請用 F12 看官網實際 HTML 改掉）──
    # import requests
    # from bs4 import BeautifulSoup
    #
    # html = requests.get("https://tpap.gov.taipei/app37/rentView/index", timeout=10).text
    # soup = BeautifulSoup(html, "html.parser")
    #
    # def to_int(text: str) -> int:
    #     text = (text or "").strip()
    #     return int(text) if text.isdigit() else 0
    #
    # result = []
    # for card in soup.select(".item"):                         # ← 每款輔具的區塊
    #     result.append(StockItem(
    #         variant_id=card["data-id"],                        # ← 款式代碼
    #         stock=to_int(card.select_one(".stock").text),      # ← 剩餘數量
    #         waiting=to_int(card.select_one(".waiting").text),  # ← 等待人數
    #     ))
    # return result
    raise NotImplementedError("fetch_stock 尚未實作")
