"""臺北市二手輔具公開頁面的解析與單次快照；不讀取個人資料或送出表單。"""

from dataclasses import dataclass
import re
from threading import Lock
import time
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from .schemas import CatalogCategory, StockItem

BASE = "https://tpap.gov.taipei"
CATALOG_URL = BASE + "/app37/rentView/additem"
SNAPSHOT_TTL_SECONDS = 30
REQUEST_INTERVAL_SECONDS = 1.0


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def soup_of(body: bytes | str) -> BeautifulSoup:
    return BeautifulSoup(body, "html.parser")


def main_content(soup: BeautifulSoup):
    return soup.select_one(".col-md-9") or soup.select_one(".essay") or soup.select_one("main") or soup


def parse_categories(body: bytes | str, url: str = CATALOG_URL) -> list[dict]:
    result = []
    for card in main_content(soup_of(body)).select("div.ind-tab"):
        img = card.select_one('img[src*="/showvehiclemodel/"]')
        if not img:
            continue
        match = re.search(r"/showvehiclemodel/(\d+)", img["src"])
        if not match:
            continue
        button = card.select_one('[onclick*="/vehicleDetail/"]')
        path = re.search(r"['\"]([^'\"]*/vehicleDetail/\d+)['\"]", button.get("onclick", "")) if button else None
        if not path:
            raise ValueError("分類有代碼卻找不到公開細項連結")
        result.append({"id": match[1], "name": clean(img.get("alt", "")).removesuffix("圖片"),
                       "image": urljoin(url, img["src"]), "detail_url": urljoin(url, path[1])})
    if not result:
        raise ValueError("沒有找到分類；官網結構可能改變")
    return result


def parse_attrs(specs: list[str]) -> dict | None:
    text = " ".join(specs)
    attrs = dict.fromkeys(("height_min", "height_max", "seat_width_in", "weight_max_kg"))
    height = re.search(r"(?:適用)?身高\s*[：:]?\s*(\d+(?:\.\d+)?)\s*[~～–—\-至]\s*(\d+(?:\.\d+)?)\s*(?:公分|cm)", text, re.I)
    if height:
        attrs.update(height_min=float(height[1]), height_max=float(height[2]))
    # 「15或16吋」不能壓成單一座寬；保留 specs，attrs 留空。
    seat = re.search(r"座寬\s*[：:]?\s*(\d+(?:\.\d+)?)\s*(吋|英吋|公分|cm)(?!\s*(?:或|至|~|～))", text, re.I)
    if seat:
        attrs["seat_width_in"] = round(float(seat[1]) / (2.54 if seat[2].lower() in ("公分", "cm") else 1), 4)
    weight = re.search(r"(?:承重|載重|最大承重)\s*[：:]?\s*(\d+(?:\.\d+)?)\s*(?:公斤|kg)", text, re.I)
    if not weight:
        weight = re.search(r"體重\s*(\d+(?:\.\d+)?)\s*(?:公斤|kg)\s*以下", text, re.I)
    if weight:
        attrs["weight_max_kg"] = float(weight[1])
    return attrs if any(v is not None for v in attrs.values()) else None


def labelled_count(text: str, label: str) -> int | None:
    match = re.search(label + r"\s*[:：]\s*(.*?)\s*$", text)
    if match is None:
        return None
    value = match[1].strip()
    if value in ("", "-", "－", "—", "無"):
        return 0
    return int(value) if re.fullmatch(r"\d+", value) else None


def parse_variants(body: bytes | str, url: str) -> tuple[list[dict], list[dict]]:
    variants, observations = [], []
    for table in main_content(soup_of(body)).select("table.ind-tab"):
        img = table.select_one('img[src*="/showvehiclemodeltype/"]')
        match = re.search(r"/showvehiclemodeltype/(\d+)", img["src"]) if img else None
        if not match:
            continue
        rows = table.find_all("tr", recursive=False) or table.select("tr")
        if len(rows) < 3 or not table.select_one("th"):
            raise ValueError(f"款式 {match[1]} 表格結構不完整")
        cells = rows[1].find_all("td", recursive=False)
        specs = []
        for cell in cells[:2]:
            for line in cell.get_text("\n", strip=True).splitlines():
                value = clean(line)
                if value and value not in ("---", "-", "無"):
                    specs.append(value)
        description_cell = rows[2].find("td")
        description = clean(description_cell.get_text(" ", strip=True)) if description_cell else ""
        text = table.get_text(" ", strip=True)
        variants.append({"id": match[1], "name": clean(table.select_one("th").get_text(" ", strip=True)),
                         "image": urljoin(url, img["src"]), "specs": specs,
                         "description": description or None, "attrs": parse_attrs(specs)})
        stock_cell = cells[-1].get_text(" ", strip=True) if len(cells) >= 3 else ""
        waiting_cell = rows[2].find_all("td", recursive=False)[-1].get_text(" ", strip=True)
        stock = labelled_count(stock_cell, "剩餘")
        waiting = labelled_count(waiting_cell, "等待人數")
        waiting_observed = waiting
        waiting_basis = "官網顯示的數值"
        # 已驗證官網有庫存時只顯示「預約」按鈕、沒有候補欄。
        # 按 README 的空白→0 規則處理，另存依據以區別直接觀測值。
        reserve = table.select_one('[onclick*="/chooseCenterCategory/"]')
        if waiting is None and "等待人數" not in text and reserve is not None and stock is not None and stock > 0:
            waiting, waiting_basis = 0, "預約可用、候補欄未顯示；依 README 空白轉 0"
        observations.append({"variant_id": match[1], "stock": stock, "waiting": waiting,
                             "waiting_observed": waiting_observed, "waiting_basis": waiting_basis,
                             "source_url": url})
    if not variants:
        raise ValueError("分類頁沒有任何款式，不能當成空庫存")
    return variants, observations

@dataclass(frozen=True)
class BorrowSnapshot:
    catalog: tuple[CatalogCategory, ...]
    stock: tuple[StockItem, ...]


_snapshot: BorrowSnapshot | None = None
_snapshot_at = 0.0
_snapshot_lock = Lock()


def _load_snapshot() -> BorrowSnapshot:
    categories, stock, category_ids, variant_ids = [], [], set(), set()
    with httpx.Client(follow_redirects=True, timeout=httpx.Timeout(30, connect=10),
                      headers={"User-Agent": "TownPass-AssistiveCrawler/0.1"}) as client:
        response = client.get(CATALOG_URL)
        response.raise_for_status()
        pending = parse_categories(response.content)
        for category in pending:
            cid = category["id"]
            if cid in category_ids or not category["name"]:
                raise ValueError("官網分類代碼重複或名稱缺漏")
            category_ids.add(cid)
            url = category["detail_url"]
            parsed = urlparse(url)
            if (parsed.scheme != "https" or parsed.hostname != "tpap.gov.taipei"
                    or parsed.path != f"/app37/rentView/vehicleDetail/{cid}" or parsed.query):
                raise ValueError("分類頁連結不是預期的官方公開資料頁")
            time.sleep(REQUEST_INTERVAL_SECONDS)
            response = client.get(url)
            response.raise_for_status()
            variants, observations = parse_variants(response.content, url)
            for variant, observation in zip(variants, observations, strict=True):
                vid = variant["id"]
                if vid in variant_ids or not variant["name"]:
                    raise ValueError("官網款式代碼重複或名稱缺漏")
                variant_ids.add(vid)
                if observation["stock"] is None or observation["waiting"] is None:
                    raise ValueError(f"款式 {vid} 數值不完整；不將抓取失敗當作零庫存")
                stock.append(StockItem(variant_id=vid, stock=observation["stock"],
                                       waiting=observation["waiting"]))
            categories.append(CatalogCategory(
                id=cid, name=category["name"], image=category["image"], variants=variants))
    if not categories or not stock:
        raise ValueError("官網沒有可驗證的輔具資料")
    return BorrowSnapshot(tuple(categories), tuple(stock))


def get_borrow_snapshot() -> BorrowSnapshot:
    """同一 process 30 秒內共用完整快照；抓取失敗不回傳空清單或舊快照。"""
    global _snapshot, _snapshot_at
    with _snapshot_lock:
        if _snapshot is not None and time.monotonic() - _snapshot_at < SNAPSHOT_TTL_SECONDS:
            return _snapshot
        fresh = _load_snapshot()
        _snapshot, _snapshot_at = fresh, time.monotonic()
        return fresh

