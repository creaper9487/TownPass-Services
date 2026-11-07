"""提供借用及評估服務的三間中心；少變動資料依 README 保存為常數。"""

from .schemas import Center

# 2026-11-07 核對：
# 地址、電話、時段：https://tpap.gov.taipei/app37/rentView/intaipei
# 服務區域：cognitionView/index（合宜）、detail3（南區）、detail2（西區）。
# 座標取上述官方介紹頁嵌入的 Google Maps 地點標記，並核對名稱、地址與電話。
# 例：https://maps.google.com/maps?q=臺北市合宜輔具中心&output=embed
# 為建物位置，並非無障礙入口或室內樓層座標；runtime 不呼叫 Google API。
_CENTERS = (
    {
        "id": "heyi", "name": "臺北市合宜輔具中心",
        "address": "臺北市中山區玉門街1號", "phone": "02-77137760",
        "districts": ["中山區", "大同區", "士林區", "北投區"],
        "open_days": [2, 3, 4, 5, 6], "lat": 25.0701455, "lng": 121.5217556,
    },
    {
        "id": "south", "name": "臺北市南區輔具中心",
        "address": "臺北市信義區大道路116號3樓之2（廣慈衛福大樓西2門）", "phone": "02-27207364",
        "districts": ["內湖區", "信義區", "文山區", "南港區"],
        "open_days": [1, 2, 3, 4, 5], "lat": 25.0386824, "lng": 121.5823037,
    },
    {
        "id": "west", "name": "臺北市西區輔具中心",
        "address": "臺北市中山區長安西路5巷2號1、2樓", "phone": "02-25237902",
        "districts": ["中正區", "萬華區", "大安區", "松山區"],
        "open_days": [2, 3, 4, 5, 6], "lat": 25.0504365, "lng": 121.5208104,
    },
)


def fetch_centers() -> list[Center]:
    """回傳 heyi/south/west，星期 1～7，保留上午與下午兩段開館時間。"""
    return [Center(**data, hours=[{"from": "09:00", "to": "12:00"},
                                  {"from": "13:30", "to": "17:00"}]) for data in _CENTERS]
