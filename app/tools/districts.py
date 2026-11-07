"""居住行政區 → 服務中心對照（評估、維修、回收依居住地分派中心）。

來源：官方網站說明（規格文件「現況與限制」）。
"""

CENTER_IDS = ("heyi", "south", "west")

DISTRICT_TO_CENTER: dict[str, str] = {
    # 合宜輔具中心
    "中山區": "heyi",
    "大同區": "heyi",
    "士林區": "heyi",
    "北投區": "heyi",
    # 南區輔具中心
    "內湖區": "south",
    "信義區": "south",
    "文山區": "south",
    "南港區": "south",
    # 西區輔具中心
    "中正區": "west",
    "萬華區": "west",
    "大安區": "west",
    "松山區": "west",
}


def center_for_district(district: str) -> str | None:
    """回傳負責該行政區的 center_id；不在臺北市回 None。"""
    return DISTRICT_TO_CENTER.get(district)
