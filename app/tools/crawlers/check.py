"""爬蟲自我檢查：執行爬蟲 function，並用 schemas.py 驗證格式。

在專案根目錄執行：
    python -m app.tools.crawlers.check catalog
    python -m app.tools.crawlers.check stock
    python -m app.tools.crawlers.check centers
    python -m app.tools.crawlers.check calendar
    python -m app.tools.crawlers.check all
"""

import json
import sys
from datetime import date

from pydantic import TypeAdapter, ValidationError

from app.tools.crawlers import fetch_catalog, fetch_center_calendar, fetch_centers, fetch_stock
from app.tools.crawlers.schemas import CalendarDay, CatalogCategory, Center, StockItem

CHECKS = {
    "catalog": (lambda: fetch_catalog(), list[CatalogCategory]),
    "stock": (lambda: fetch_stock(), list[StockItem]),
    "centers": (lambda: fetch_centers(), list[Center]),
    "calendar": (lambda: fetch_center_calendar("heyi", date.today(), 14), list[CalendarDay]),
}


def _extra_checks(name: str, data: list) -> list[str]:
    problems = []
    if name == "catalog":
        ids = [v.variant_id for c in data for v in c.variants]
        if len(ids) != len(set(ids)):
            problems.append("variant_id 有重複")
        print(f"  類別 {len(data)} 個、品項 {len(ids)} 種（官網約 12 類 62 種）")
    elif name == "stock":
        ids = [s.variant_id for s in data]
        if len(ids) != len(set(ids)):
            problems.append("variant_id 有重複")
        try:
            catalog_ids = {v.variant_id for c in TypeAdapter(list[CatalogCategory]).validate_python(
                fetch_catalog(), from_attributes=True) for v in c.variants}
            missing = set(ids) - catalog_ids
            if missing:
                problems.append(f"這些 variant_id 在 catalog 裡找不到：{sorted(missing)[:10]}")
        except NotImplementedError:
            print("  （fetch_catalog 還沒寫，略過 variant_id 對照）")
        print(f"  共 {len(data)} 筆")
    elif name == "centers":
        got = sorted(c.center_id for c in data)
        if got != ["heyi", "south", "west"]:
            problems.append(f"center_id 應該剛好是 heyi / south / west，拿到 {got}")
    elif name == "calendar":
        if len(data) != 14:
            problems.append(f"要 14 筆，拿到 {len(data)} 筆")
        for i, d in enumerate(data):
            if (d.date - date.today()).days != i:
                problems.append(f"第 {i} 筆日期不連續：{d.date}")
                break
            if d.is_open and not (d.open and d.close):
                problems.append(f"{d.date} 有開館但沒填 open / close")
    return problems


def run(name: str) -> bool:
    fn, result_type = CHECKS[name]
    print(f"[{name}]")
    try:
        raw = fn()
    except NotImplementedError:
        print("  還沒實作")
        return False
    try:
        data = TypeAdapter(result_type).validate_python(raw, from_attributes=True)
    except ValidationError as exc:
        print("  ✗ 格式錯誤：")
        for err in exc.errors()[:10]:
            print(f"    {'.'.join(map(str, err['loc']))}: {err['msg']}")
        return False
    problems = _extra_checks(name, data)
    for p in problems:
        print(f"  ✗ {p}")
    if not problems:
        sample = TypeAdapter(result_type).dump_python(data[:2], mode="json")
        print("  ✓ 格式正確，前兩筆：")
        print("   ", json.dumps(sample, ensure_ascii=False)[:500])
    return not problems


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    names = list(CHECKS) if target == "all" else [target]
    ok = all([run(n) for n in names])
    sys.exit(0 if ok else 1)
