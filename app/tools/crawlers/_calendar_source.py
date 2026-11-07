"""開館日：中心每週時段、具名政府假日及可辨識的官方休館公告。"""

import calendar
from collections import deque
import csv
from datetime import date, datetime, timedelta
from functools import lru_cache
import io
import re
from threading import Lock
import time
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.tools.logger import get_logger

from .centers import fetch_centers
from .schemas import CalendarDay, CenterId

BASE = "https://tpap.gov.taipei"
# 官方資料集 https://data.gov.tw/dataset/14718 的 115、116 年 CSV。
GOVERNMENT_CALENDARS = {2026: (
    "https://www.dgpa.gov.tw/FileConversion?filename=dgpa%2Ffiles%2F202506%2F"
    "a52331bd-a189-466b-b0f0-cae3062bbf74.csv&name="
    "115%E5%B9%B4%E4%B8%AD%E8%8F%AF%E6%B0%91%E5%9C%8B%E6%94%BF%E5%BA%9C"
    "%E8%A1%8C%E6%94%BF%E6%A9%9F%E9%97%9C%E8%BE%A6%E5%85%AC%E6%97%A5"
    "%E6%9B%86%E8%A1%A8.csv&nfix="
), 2027: (
    "https://www.dgpa.gov.tw/FileConversion?filename=dgpa%2Ffiles%2F202607%2F"
    "f538b1ff-ba60-4c63-9477-10db8e6612d1.csv&name="
    "116%E5%B9%B4%E4%B8%AD%E8%8F%AF%E6%B0%91%E5%9C%8B%E6%94%BF%E5%BA%9C"
    "%E8%A1%8C%E6%94%BF%E6%A9%9F%E9%97%9C%E8%BE%A6%E5%85%AC%E6%97%A5"
    "%E6%9B%86%E8%A1%A8_utf8bom.csv&nfix="
)}
logger = get_logger(__name__)
_CENTER_NAMES = {"合宜": "heyi", "南區": "south", "西區": "west"}
_DATE_PATTERN = re.compile(r"(\d{3,4})[年/.-](\d{1,2})[月/.-](\d{1,2})日?")
_closures: dict[tuple[str, date], str] | None = None
_closures_at = 0.0
_closures_lock = Lock()


def _get(client: httpx.Client, url: str) -> bytes:
    response = client.get(url)
    response.raise_for_status()
    return response.content


def parse_holidays(body: bytes, year: int) -> dict[date, str]:
    rows = list(csv.DictReader(io.StringIO(body.decode("utf-8-sig"))))
    expected = 366 if calendar.isleap(year) else 365
    if len(rows) != expected or not {"西元日期", "是否放假", "備註"}.issubset(rows[0]):
        raise ValueError("政府日曆欄位或全年筆數不符")
    all_days, holidays = set(), {}
    for row in rows:
        day = datetime.strptime(row["西元日期"].strip(), "%Y%m%d").date()
        flag, note = row["是否放假"].strip(), row["備註"].strip()
        if day.year != year or day in all_days or flag not in ("0", "2"):
            raise ValueError("政府日曆日期或休假標記不符")
        all_days.add(day)
        # 合宜／西區例行星期六開館；不能把政府每個週末當中心國定假日。
        if flag == "2" and (note or day.isoweekday() <= 5):
            holidays[day] = note or "政府公告放假"
    return holidays


@lru_cache(maxsize=3)
def _load_holidays(year: int) -> dict[date, str]:
    if year not in GOVERNMENT_CALENDARS:
        raise NotImplementedError(f"尚未設定 {year} 年官方日曆來源，不能推測開館日")
    with httpx.Client(follow_redirects=True, timeout=20) as client:
        return parse_holidays(_get(client, GOVERNMENT_CALENDARS[year]), year)


def _source_date(match) -> date:
    year, month, day = map(int, match.groups())
    return date(year + 1911 if year < 1911 else year, month, day)


def parse_closure_notice(body: bytes) -> dict[tuple[str, date], str]:
    """只採有中心名稱及明確日期的文字，截去「將於…開館」以免誤關恢復日。"""
    soup = BeautifulSoup(body, "html.parser")
    content = soup.select_one(".col-md-9")
    if content is None:
        raise ValueError("休館公告缺少內容區塊")
    result = {}
    for paragraph in content.select("p, li"):
        text = paragraph.get_text(" ", strip=True)
        if "休館" not in text:
            continue
        closed_part = re.split(r"將於|恢復|開館服務|開放服務", text, maxsplit=1)[0]
        before_closed = closed_part.split("休館", 1)[0]
        if _DATE_PATTERN.search(before_closed):
            closed_part = before_closed + "休館"
        centers = [cid for name, cid in _CENTER_NAMES.items() if name in closed_part]
        matches = list(_DATE_PATTERN.finditer(closed_part))
        if not centers or not matches:
            continue
        days = [_source_date(m) for m in matches]
        if len(days) == 1:
            # 例如 115/10/9~10/12。
            short_end = re.search(r"[~～至]\s*(\d{1,2})[月/.-](\d{1,2})日?", closed_part[matches[0].end():])
            if short_end:
                days.append(date(days[0].year, int(short_end[1]), int(short_end[2])))
        is_range = len(days) == 2 and re.search(r"[~～至]", closed_part)
        if is_range:
            if not 0 <= (days[1] - days[0]).days <= 60:
                raise ValueError("休館日期範圍不合理，需人工確認")
            days = [days[0] + timedelta(days=i) for i in range((days[1] - days[0]).days + 1)]
        for cid in centers:
            for day in days:
                result[cid, day] = "中心公告休館"
    if not result:
        raise ValueError("休館公告無法對應中心與日期，需人工確認")
    return result


def _reviewed_closures() -> dict[tuple[str, date], str]:
    # 已人工核對的歷史公告：/app37/newsView/detail?newsid=252，115/09/29。
    # 公告到期後可能不在最新消息中，仍保留已核定的日期。
    result = {("south", date(2026, 10, 9)): "國慶連假（中心公告）"}
    for cid in ("heyi", "west"):
        for offset in range(4):
            result[cid, date(2026, 10, 9) + timedelta(days=offset)] = "國慶連假（中心公告）"
    return result


def _fetch_closures() -> dict[tuple[str, date], str]:
    pending, visited, notices = deque([BASE + "/app37/newsView/index"]), set(), set()
    result = _reviewed_closures()
    # 單則公告暫時讀不懂時，仍保留此前已成功確認的休館日期。
    if _closures is not None:
        result.update(_closures)
    with httpx.Client(follow_redirects=True, timeout=20,
                      headers={"User-Agent": "TownPass-AssistiveCrawler/0.1"}) as client:
        while pending:
            url = pending.popleft()
            if url in visited:
                continue
            if len(visited) >= 20:
                raise ValueError("公告分頁超過 20 頁，不能假設已檢查完休館資訊")
            if visited:
                time.sleep(1)
            visited.add(url)
            soup = BeautifulSoup(_get(client, url), "html.parser")
            content = soup.select_one(".col-md-9")
            if content is None or not content.select_one("h2"):
                raise ValueError("最新消息網頁結構改變")
            for anchor in content.select("a[href]"):
                href = urljoin(url, anchor["href"])
                parsed = urlparse(href)
                if parsed.scheme != "https" or parsed.hostname != "tpap.gov.taipei":
                    continue
                if parsed.path == "/app37/newsView/query" and href not in visited:
                    pending.append(href)
                elif parsed.path == "/app37/newsView/detail":
                    card = anchor.find_parent("div", class_="row") or anchor.parent
                    if "休館" in card.get_text(" ", strip=True):
                        notices.add(href)
        for url in sorted(notices):
            time.sleep(1)
            try:
                result.update(parse_closure_notice(_get(client, url)))
            except Exception as exc:
                # 不輸出例外本文、HTML 或 URL，以免第三方內容含有個資。
                logger.warning("Skipping unavailable or unreadable closure notice (%s)",
                               type(exc).__name__)
    return result


def _load_closures() -> dict[tuple[str, date], str]:
    """公告為可降級資料源；失敗沿用已知資料，五分鐘後再嘗試。"""
    global _closures, _closures_at
    with _closures_lock:
        if _closures is not None and time.monotonic() - _closures_at < 300:
            return _closures
        try:
            fresh = _fetch_closures()
        except Exception as exc:
            fallback = "last known result" if _closures is not None else "reviewed closures"
            logger.warning("Closure refresh failed (%s); using %s",
                           type(exc).__name__, fallback)
            fresh = _closures if _closures is not None else _reviewed_closures()
        # 失敗也暫存回退結果，避免每次借用請求都重試不可用的官網。
        _closures, _closures_at = fresh, time.monotonic()
        return fresh


def fetch_calendar(center_id: CenterId, start: date, days: int) -> list[CalendarDay]:
    if not 1 <= days <= 366:
        raise ValueError("days 必須介於 1～366")
    center = next((c for c in fetch_centers() if c.id == center_id), None)
    if center is None:
        raise ValueError("未知的輔具中心")
    end = start + timedelta(days=days - 1)
    holidays = {}
    for year in range(start.year, end.year + 1):
        holidays.update(_load_holidays(year))
    closures = _load_closures()
    result = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        reason = closures.get((center_id, day)) or holidays.get(day)
        if not reason and day.isoweekday() not in center.open_days:
            reason = "例假日休館"
        result.append(CalendarDay(date=day, open=reason is None,
                                  hours=[h.model_copy() for h in center.hours] if reason is None else [],
                                  reason=reason))
    return result
