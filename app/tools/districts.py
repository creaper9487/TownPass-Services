"""臺北市行政區 → 服務中心對照。本系統只服務臺北市。

評估、維修、回收依「居住行政區」分派中心；借用由使用者自選中心。
來源：官方網站說明（規格文件「現況與限制」）。
"""

from typing import Literal

CENTER_IDS = ("heyi", "south", "west")

# 臺北市 12 個行政區（前端下拉選單只能選這些）
TaipeiDistrict = Literal[
    "中正區", "大同區", "中山區", "松山區", "大安區", "萬華區",
    "信義區", "士林區", "北投區", "內湖區", "南港區", "文山區",
]

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


def center_for_district(district: str) -> str:
    """回傳負責該臺北市行政區的 center_id。"""
    return DISTRICT_TO_CENTER[district]
