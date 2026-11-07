"""僅涵蓋輔具借用、評估入口的公開資料試跑。

執行：python -m scripts.preview --core-only
借用／評估來源：python -m scripts.preview
輸出說明見 PREVIEW.md。只發送 GET，不送出預約或候補表單。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from pydantic import TypeAdapter, ValidationError

from app.tools.crawlers.schemas import CalendarDay, CatalogCategory, Center, StockItem
from app.tools.crawlers.centers import fetch_centers
from app.tools.crawlers.center_calendar import fetch_center_calendar
from app.tools.crawlers._borrow_source import (clean, soup_of, main_content, parse_categories,
                                              parse_attrs, labelled_count, parse_variants)


ROOT = Path(__file__).resolve().parents[1]
TAIPEI = timezone(timedelta(hours=8))
BASE = "https://tpap.gov.taipei"
CATALOG_URL = BASE + "/app37/rentView/additem"
ALLOWED_HOSTS = {"tpap.gov.taipei", "tpap.taipei"}
PUBLIC_PAGES = {
    "borrowing_rules": BASE + "/app37/rentView/intaipei",
    "evaluation_entry": BASE + "/app37/otherReserveView/where",
}


def now() -> str:
    return datetime.now(TAIPEI).isoformat(timespec="seconds")








def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    keys = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v
                             for k, v in row.items()})


def read_csv(body: bytes) -> list[dict[str, str]]:
    for encoding in ("utf-8-sig", "cp950"):
        try:
            text = body.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("CSV 不是 UTF-8 或 CP950")
    if "<html" in text[:500].lower() or "<!doctype" in text[:500].lower():
        raise ValueError("CSV 來源實際回傳 HTML，不能當成資料")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or len(reader.fieldnames) < 2:
        raise ValueError("CSV 缺少預期的多欄表頭")
    return [{clean(k): clean(v or "") for k, v in row.items() if k is not None} for row in reader]


@dataclass
class Document:
    body: bytes
    url: str
    fetched_at: str
    cached: bool


class PublicClient:
    """限官方來源的一次性 GET；快取不儲存 Cookie、隱藏欄位或腳本。"""

    def __init__(self, cache: Path, reuse: bool = False, delay: float = 1.0):
        self.cache, self.reuse, self.delay = cache, reuse, delay
        cache.mkdir(parents=True, exist_ok=True)
        self.client = httpx.Client(follow_redirects=True, timeout=httpx.Timeout(60, connect=15),
                                   headers={"User-Agent": "TownPass-AssistiveDataPreview/0.1"})
        self.manifest: list[dict] = []
        self.documents: dict[str, Document] = {}
        self.last_request: dict[str, float] = {}

    def close(self):
        self.client.close()

    def get(self, url: str) -> Document:
        if url in self.documents:
            return self.documents[url]
        host = urlparse(url).hostname
        if host not in ALLOWED_HOSTS or any(p in url for p in ("waitingRent/", "cancelRent/")):
            raise ValueError("拒絕非資料來源或操作類網址")
        key = hashlib.sha256(url.encode()).hexdigest()
        body_path, meta_path = self.cache / (key + ".body"), self.cache / (key + ".json")
        cached = self.reuse and body_path.exists() and meta_path.exists()
        if cached:
            metadata = json.loads(meta_path.read_text(encoding="utf-8"))
            body = body_path.read_bytes()
        else:
            wait = self.delay - (time.monotonic() - self.last_request.get(host, 0))
            if wait > 0:
                time.sleep(wait)
            self.last_request[host] = time.monotonic()
            response = self.client.get(url)
            response.raise_for_status()
            body = response.content
            if "html" in response.headers.get("content-type", ""):
                soup = soup_of(body)
                for node in soup.select('script, input[type="hidden"], input[type="password"]'):
                    node.decompose()
                for node in soup.select("input[value]"):
                    del node["value"]
                body = str(soup).encode("utf-8")
            metadata = {"url": url, "response_url": str(response.url), "fetched_at": now(),
                        "status": response.status_code, "content_type": response.headers.get("content-type")}
            body_path.write_bytes(body)
            write_json(meta_path, metadata)
        self.manifest.append({**metadata, "cached": cached, "bytes": len(body),
                              "saved_body_sha256": hashlib.sha256(body).hexdigest()})
        document = Document(body, url, metadata["fetched_at"], cached)
        self.documents[url] = document
        return document












def build_calendar(center: dict, start: date, days: int, government_rows: list[dict]) -> list[dict]:
    holidays = {}
    for row in government_rows:
        value = re.sub(r"\D", "", row.get("西元日期", ""))
        note = row.get("備註", "").strip()
        # 政府表的星期六休假不代表合宜、西區也休館；只採明確有名稱的假日。
        if len(value) == 8 and row.get("是否放假") == "2" and note:
            holidays[datetime.strptime(value, "%Y%m%d").date()] = note
    result = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        reason = holidays.get(day)
        if not reason and day.isoweekday() not in center["open_days"]:
            reason = "例假日休館"
        result.append({"date": day.isoformat(), "open": reason is None,
                       "hours": center["hours"] if reason is None else [], "reason": reason})
    return result


def table_rows(table) -> list[list[str]]:
    """展開 rowspan/colspan，保留服務據點表的中心歸屬。"""
    matrix: dict[tuple[int, int], str] = {}
    rows = table.select("tr")
    for r, tr in enumerate(rows):
        col = 0
        for cell in tr.find_all(("td", "th"), recursive=False):
            while (r, col) in matrix:
                col += 1
            rowspan, colspan = int(cell.get("rowspan", 1)), int(cell.get("colspan", 1))
            value = clean(cell.get_text(" ", strip=True))
            for rr in range(r, r + rowspan):
                for cc in range(col, col + colspan):
                    matrix[(rr, cc)] = value
            col += colspan
    width = max((col for _, col in matrix), default=-1) + 1
    return [[matrix.get((r, col), "") for col in range(width)] for r in range(len(rows))]


class Preview:
    def __init__(self, output: Path, client: PublicClient):
        self.output, self.client = output, client
        self.output.mkdir(parents=True, exist_ok=True)
        self.counts: dict[str, int] = {}
        self.issues: list[dict] = []
        self.failures: list[dict] = []
        self.validation: dict[str, dict] = {}
        self.sample_records: list[dict] = []

    def issue(self, section: str, message: str):
        self.issues.append({"section": section, "message": message})

    def run(self, name: str, function):
        print(f"[{now()}] {name} ...", flush=True)
        try:
            function()
        except (httpx.HTTPError, ValueError, KeyError, OSError, NotImplementedError) as exc:
            self.issue(name, f"{type(exc).__name__}: {exc}")
            self.failures.append({"section": name, "error": type(exc).__name__})
            print(f"  未完成：{type(exc).__name__}；詳見 summary.json", flush=True)

    def validate(self, name: str, data, model):
        try:
            TypeAdapter(model).validate_python(data)
            self.validation[name] = {"valid": True, "records": len(data)}
        except ValidationError as exc:
            self.validation[name] = {"valid": False, "records": len(data),
                                     "errors": [{"field": list(e["loc"]), "message": e["msg"]} for e in exc.errors()]}


    def catalog_stock(self):
        categories = parse_categories(self.client.get(CATALOG_URL).body)
        catalog, observations = [], []
        for category in categories:
            url = category.pop("detail_url")
            variants, counts = parse_variants(self.client.get(url).body, url)
            catalog.append({**category, "variants": variants})
            observations.extend(counts)
            print(f"  {category['name']}：{len(variants)} 款", flush=True)
        ids = [v["id"] for c in catalog for v in c["variants"]]
        if len(set(ids)) != len(ids):
            raise ValueError("官網款式代碼重複，請檢查解析結果")
        stock = [{k: row[k] for k in ("variant_id", "stock", "waiting")}
                 for row in observations if row["stock"] is not None and row["waiting"] is not None]
        missing = sorted(set(ids) - {s["variant_id"] for s in stock})
        if missing:
            self.issue("stock", f"以下款式數值不明，保留原始觀測、不填假 0：{missing}")
        write_json(self.output / "catalog.json", catalog)
        write_json(self.output / "stock.json", stock)
        write_json(self.output / "stock_observations.json", observations)
        flat = [{"category_id": c["id"], "category": c["name"], **v} for c in catalog for v in c["variants"]]
        write_csv(self.output / "catalog.csv", flat)
        write_csv(self.output / "stock.csv", stock)
        by_id = {s["variant_id"]: s for s in stock}
        joined = [{"variant_id": v["id"], "category": c["name"], "name": v["name"],
                   "specs": "；".join(v["specs"]), "stock": by_id.get(v["id"], {}).get("stock"),
                   "waiting": by_id.get(v["id"], {}).get("waiting"), "image": v["image"]}
                  for c in catalog for v in c["variants"]]
        write_csv(self.output / "availability_preview.csv", joined)
        self.sample_records = joined[:3] + [r for r in joined if (r["stock"] or 0) > 0][:2]
        self.counts.update(categories=len(catalog), variants=len(ids), stock=len(stock))
        self.counts["available_variants"] = sum(s["stock"] > 0 for s in stock)
        self.counts["stock_total"] = sum(s["stock"] for s in stock)
        self.counts["waiting_blank_mapped_to_zero"] = sum(r["waiting_observed"] is None and r["waiting"] == 0 for r in observations)
        self.validate("catalog", catalog, list[CatalogCategory])
        self.validate("stock", stock, list[StockItem])
        self.validation["catalog_stock_ids"] = {"valid": not missing, "missing_stock_ids": missing}
        self.issue("stock", "本次是各分類依序抓取的快照，並非同一瞬間的庫存；官網未提供各中心分庫存。")

    def centers_calendar(self, start: date, days: int):
        centers = [c.model_dump(mode="json", by_alias=True) for c in fetch_centers()]
        write_json(self.output / "centers.json", centers)
        write_json(self.output / "centers_preview.json", centers)
        self.validate("centers", centers, list[Center])
        self.counts["centers"] = len(centers)
        calendars = {
            c["id"]: [d.model_dump(mode="json", by_alias=True)
                      for d in fetch_center_calendar(c["id"], start, days)]
            for c in centers
        }
        write_json(self.output / "calendar_preview.json", calendars)
        for cid, values in calendars.items():
            self.validate("calendar_" + cid, values, list[CalendarDay])
        self.counts["calendar_days"] = sum(map(len, calendars.values()))
        self.issue("calendar", "已接入每週時段、2026～2027 年官方日曆與文字休館公告；公告失敗沿用最近成功結果或已核對資料，略過的影像型公告需人工核對。")

    def public_page(self, key: str, url: str):
        document = self.client.get(url)
        soup = soup_of(document.body)
        content = main_content(soup)
        for node in content.select("nav, footer, header"):
            node.decompose()
        payload = {
            "source_url": url, "fetched_at": document.fetched_at,
            "title": clean(soup.title.get_text()) if soup.title else "",
            "text": content.get_text("\n", strip=True),
            "tables": [table_rows(t) for t in content.select("table")],
            "links": [{"text": clean(a.get_text(" ", strip=True)), "url": urljoin(url, a["href"])}
                      for a in content.select("a[href]") if not a["href"].startswith(("javascript:", "#"))],
            "public_form_fields": [{"tag": node.name, "name": node.get("name"), "type": node.get("type"),
                                    "options": [{"label": clean(o.get_text()), "value": o.get("value")}
                                                for o in node.select("option")]}
                                   for node in content.select("select, textarea, input[name]")],
        }
        if not payload["text"]:
            raise ValueError("公開頁面沒有可讀內容")
        write_json(self.output / "pages" / f"{key}.json", payload)
        self.counts[key + "_tables"] = len(payload["tables"])
        if key == "evaluation_entry" and not payload["public_form_fields"]:
            self.issue(key, "此頁僅為服務資格／入口說明，尚未取得完整申請表欄位；沒有送出表單。")
        return payload

    def finish(self):
        write_json(self.output / "source_manifest.json", self.client.manifest)
        report = {"generated_at": now(), "output_dir": str(self.output), "counts": self.counts,
                  "schema_validation": self.validation, "issues": self.issues,
                  "collection_failures": self.failures, "backend_ready": False,
                  "sample_records": self.sample_records,
                  "mode": "borrow/evaluation public data preview; four data functions integrated"}
        write_json(self.output / "summary.json", report)
        lines = ["# 輔具公開資料爬蟲試跑", "", f"產生時間：{report['generated_at']}", "", "## 本次筆數", ""]
        lines.extend(f"- {key}: {value}" for key, value in self.counts.items())
        lines.extend(["", "## 品項預覽", "", "| 款式 ID | 類別 | 品項 | 規格 | 剩餘 | 候補 |",
                      "|---|---|---|---|---:|---:|"])
        lines.extend("| " + " | ".join(str(row.get(k, "")).replace("|", "／")
                                     for k in ("variant_id", "category", "name", "specs", "stock", "waiting")) + " |"
                     for row in self.sample_records)
        lines.extend(["", "## 回傳格式檢查", ""])
        lines.extend(f"- {key}: {'通過' if value['valid'] else '尚未符合（見 summary.json）'}" for key, value in self.validation.items())
        lines.extend(["", "## 缺漏與使用限制", ""])
        lines.extend(f"- [{item['section']}] {item['message']}" for item in self.issues)
        lines.extend(["", "完整來源、抓取時間與快取狀態見 source_manifest.json。",
                      "目錄、庫存、中心及行事曆對齊 schemas.py；完整預約送件尚待中心介接。",
                      "pages 僅保留借用規則及評估入口。", ""])
        (self.output / "summary.md").write_text("\n".join(lines), encoding="utf-8")
        print(json.dumps(report["counts"], ensure_ascii=False, indent=2), flush=True)
        print(f"結果：{self.output / 'summary.md'}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core-only", action="store_true", help="先跑目錄、庫存、中心及行事曆")
    parser.add_argument("--reuse-cache", action="store_true", help="重用已存的公開回應；不代表即時庫存")
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--start", type=date.fromisoformat, default=datetime.now(TAIPEI).date())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not 1 <= args.days <= 366:
        parser.error("days 必須介於 1～366")
    folder = ROOT / ".cache" / "assistive-preview"
    output = args.output or folder / datetime.now(TAIPEI).strftime("%Y%m%d-%H%M%S")
    client = PublicClient(folder / "http", reuse=args.reuse_cache)
    preview = Preview(output, client)
    try:
        preview.run("catalog_stock", preview.catalog_stock)
        preview.run("centers_calendar", lambda: preview.centers_calendar(args.start, args.days))
        if not args.core_only:
            for key, url in PUBLIC_PAGES.items():
                preview.run(key, lambda key=key, url=url: preview.public_page(key, url))
    finally:
        preview.finish()
        client.close()
    return 1 if preview.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
