from app.tools.crawlers.schemas import Center


def fetch_centers() -> list[Center]:
    """取得 3 間輔具中心的基本資料。

    資料來源（擇一，資料很少變動，手動整理成常數也可以）：
        - https://tpap.gov.taipei/ 各中心介紹頁
        - 各中心官網「交通資訊 / 服務時間」頁
        座標可用 Google 地圖查地址後手填（約略即可，前端只拿來算「離我最近」）。

    需要的功能：
        1. 剛好回傳 3 筆，center_id 固定為：
             "heyi"  臺北市合宜輔具中心：中山、大同、士林、北投
             "south" 臺北市南區輔具中心：內湖、信義、文山、南港
             "west"  臺北市西區輔具中心：中正、萬華、大安、松山
        2. 每間要有：名稱、地址、電話、負責行政區、每週開館時段、經緯度。
        3. 開館時段若一天分上下午兩段，就放兩筆 OpeningHours。

    回傳：
        list[Center]，範例：
        [
            {
                "center_id": "heyi",
                "name": "臺北市合宜輔具中心",
                "address": "臺北市中山區…",
                "phone": "02-xxxx-xxxx",
                "districts": ["中山區", "大同區", "士林區", "北投區"],
                "opening_hours": [
                    {"weekday": 0, "open": "08:30", "close": "17:30"},
                    {"weekday": 1, "open": "08:30", "close": "17:30"}
                ],
                "lat": 25.06,
                "lng": 121.52
            }
        ]

    呼叫頻率：後端快取 1 小時。
    """
    raise NotImplementedError("fetch_centers 尚未實作")
