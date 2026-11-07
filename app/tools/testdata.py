"""測試模式（TEST_MODE=true）用的固定假資料：爬蟲不連官網，改回傳這裡的資料。

刻意做得「多筆、欄位變化多」，讓前端測相容性：
    - 目錄 12 類 62 款（跟官網一樣多）
    - 有圖 / 沒圖、規格空的 / 很多行、說明很長 / 沒有、attrs 全有 / 部分 / 沒有
    - 名稱有全形括號、斜線、英數混合、很長的名稱
    - 庫存：0 有人排隊、0 沒人排隊、1、很多、999
    - 行事曆：例假日、國定假日、臨時休館、補班、午休兩段
    - 公告：全部中心、單一中心、已結束（不該出現）、尚未開始
資料是固定的（同樣輸入永遠同樣輸出），方便寫測試、截圖比對。
"""

from datetime import date, datetime, timedelta

from app.tools.timeutil import TAIPEI

IMG = "https://picsum.photos/seed/{}/400/300"  # 測試用假圖片

CATEGORIES = [
    ("1", "輪椅類", 8), ("2", "助行器類", 7), ("3", "拐杖類", 5), ("4", "洗澡椅類", 6),
    ("5", "便盆椅類", 5), ("6", "居家照顧床類", 6), ("7", "移位輔具類", 5), ("8", "擺位輔具類", 4),
    ("9", "電動代步車類", 4), ("10", "輔助溝通類", 4), ("11", "視覺輔具類", 4), ("20", "其他", 4),
]  # 合計 62 款；最後一類代碼刻意跳號（官網也有）

_NAME_VARIANTS = [
    "一般型", "輕量型", "兒童用（小）", "加寬型 A/B", "可躺式", "高背型", "折疊式 2.0",
    "附扶手／可拆", "特殊需求加大加寬可調整角度型（含頭靠與腳靠）",
]

_SPEC_SETS = [
    [],
    ["座寬 18 吋", "重量 15 公斤"],
    ["座寬 16 吋", "適用身高 140–170 公分", "承重 100 公斤"],
    ["尺寸 60×80×90 公分"],
    ["座寬 15或16吋", "可調高度 8 段", "鋁合金", "附安全帶", "防傾桿"],
]

_DESCRIPTIONS = [
    None,
    "適合短距離移動。",
    "使用前請先由治療師評估。借用期間如有損壞請聯絡中心，不要自行修理。"
    "本輔具為二手回收再整理品，外觀可能有使用痕跡，但功能皆已檢查正常。" * 2,
]


def _attrs(i: int) -> dict | None:
    match i % 4:
        case 0:
            return None
        case 1:
            return {"seat_width_in": 18.0, "weight_max_kg": 100.0}
        case 2:
            return {"height_min": 140.0, "height_max": 170.0, "seat_width_in": 16.0, "weight_max_kg": 100.0}
        case _:
            return {"weight_max_kg": 120.0}


def _variants():
    vid = 180
    for cid, cname, count in CATEGORIES:
        for k in range(count):
            vid += 1
            i = vid - 181
            base = cname.removesuffix("類")
            yield cid, {
                "id": str(vid),
                "name": f"{_NAME_VARIANTS[i % len(_NAME_VARIANTS)]}{base}",
                "image": None if i % 5 == 4 else IMG.format(vid),
                "specs": _SPEC_SETS[i % len(_SPEC_SETS)],
                "description": _DESCRIPTIONS[i % len(_DESCRIPTIONS)],
                "attrs": _attrs(i),
            }


def fetch_catalog() -> list[dict]:
    variants: dict[str, list] = {}
    for cid, v in _variants():
        variants.setdefault(cid, []).append(v)
    return [{"id": cid, "name": name, "image": None if cid == "20" else IMG.format(f"c{cid}"),
             "variants": variants[cid]} for cid, name, _ in CATEGORIES]


def fetch_stock() -> list[dict]:
    result = []
    for cid, v in _variants():
        i = int(v["id"]) - 181
        stock, waiting = [(0, 3 + i % 21), (1, 0), (12, 0), (0, 0), (3, 2)][i % 5]
        if i == 61:
            stock, waiting = 999, 0  # 很大的數字
        result.append({"variant_id": v["id"], "stock": stock, "waiting": waiting})
    return result


CENTERS = [
    {"id": "heyi", "name": "臺北市合宜輔具中心", "address": "臺北市中山區玉門街1號", "phone": "02-77137760",
     "districts": ["中山區", "大同區", "士林區", "北投區"], "open_days": [2, 3, 4, 5, 6],
     "hours": [{"from": "09:00", "to": "12:00"}, {"from": "13:30", "to": "17:00"}],
     "lat": 25.0701455, "lng": 121.5217556},
    {"id": "south", "name": "臺北市南區輔具中心", "address": "臺北市信義區大道路116號3樓之2（廣慈衛福大樓西2門）",
     "phone": "02-27207364", "districts": ["內湖區", "信義區", "文山區", "南港區"], "open_days": [1, 2, 3, 4, 5],
     "hours": [{"from": "09:00", "to": "12:00"}, {"from": "13:30", "to": "17:00"}],
     "lat": 25.0386824, "lng": 121.5823037},
    {"id": "west", "name": "臺北市西區輔具中心", "address": "臺北市中山區長安西路5巷2號1、2樓", "phone": "02-25237902",
     "districts": ["中正區", "萬華區", "大安區", "松山區"], "open_days": [2, 3, 4, 5, 6],
     "hours": [{"from": "09:00", "to": "17:00"}],  # 刻意只有一段（沒有午休）
     "lat": 25.0504365, "lng": 121.5208104},
]


def fetch_centers() -> list[dict]:
    return CENTERS


def fetch_center_calendar(center_id: str, start: date, days: int) -> list[dict]:
    center = next(c for c in CENTERS if c["id"] == center_id)
    result = []
    for i in range(days):
        d = start + timedelta(days=i)
        if d.day == 13:
            reason = "測試國定假日"
        elif center_id == "south" and d.day == 20:
            reason = "臨時休館"
        elif d.isoweekday() not in center["open_days"] and d.day != 21:  # 每月 21 日當作補班照常開館
            reason = "例假日休館"
        else:
            reason = None
        result.append({"date": d, "open": reason is None, "hours": [] if reason else center["hours"],
                       "reason": reason})
    return result


def fetch_notices() -> list[dict]:
    t = datetime.now(TAIPEI).replace(microsecond=0)
    return [
        {"id": "test-1", "title": "【測試】系統維護公告", "body": "這是測試公告，全部中心適用。",
         "center_ids": [], "starts_at": None, "ends_at": t + timedelta(days=30), "published_at": t - timedelta(days=2)},
        {"id": "test-2", "title": "【測試】合宜輔具中心臨時休館", "body": "合宜輔具中心下週三臨時休館一天。",
         "center_ids": ["heyi"], "starts_at": t + timedelta(days=5), "ends_at": t + timedelta(days=6),
         "published_at": t - timedelta(days=1)},
        {"id": "test-3", "title": "【測試】南區、西區輔具中心連假休館（標題很長，測試換行與截斷效果用的文字）",
         "body": "南區、西區輔具中心連假期間休館。" * 5, "center_ids": ["south", "west"],
         "starts_at": t + timedelta(days=10), "ends_at": t + timedelta(days=14), "published_at": t},
        {"id": "test-old", "title": "【測試】已結束的公告（不該出現）", "body": "", "center_ids": [],
         "starts_at": t - timedelta(days=20), "ends_at": t - timedelta(days=10), "published_at": t - timedelta(days=21)},
    ]


def forward_reservation(payload: dict) -> dict:
    return {"accepted": True, "center_reference": f"TEST-{payload['reservation_id']}", "message": None}


FAKES = {
    "fetch_catalog": fetch_catalog,
    "fetch_stock": fetch_stock,
    "fetch_centers": fetch_centers,
    "fetch_center_calendar": fetch_center_calendar,
    "fetch_notices": fetch_notices,
    "forward_reservation": forward_reservation,
}
