"""借用爬蟲的離線驗證，涵蓋來源失敗、快取及取貨行事曆。"""

import csv
from datetime import date, timedelta
import io

import httpx
import pytest

from app.tools.crawlers import fetch_catalog, fetch_center_calendar, fetch_centers, fetch_stock
from app.tools.crawlers import _borrow_source as borrow
from app.tools.crawlers import _calendar_source as cal


def variant_html(vid, stock="0", waiting="13", available=False):
    button = f'''<button onclick="window.location.assign('/app37/rentView/chooseCenterCategory/{vid}')">預約</button>''' if available else ""
    queue = "" if waiting is None else f"<span>等待人數：{waiting}</span>"
    return f'''<table class="ind-tab"><tr>
    <td rowspan="3"><img src="/app37/tools/showvehiclemodeltype/{vid}"></td><th>輔具</th></tr>
    <tr><td>座寬18吋</td><td>---</td><td>剩餘:{stock}</td></tr>
    <tr><td colspan="2">說明</td><td>{button}{queue}</td></tr></table>'''


@pytest.fixture
def source(monkeypatch):
    requests, state = [], {"broken": False, "stock": "3"}
    client_class = httpx.Client

    def respond(request):
        assert request.method == "GET"
        requests.append(str(request.url))
        path = request.url.path
        if path.endswith("/additem"):
            cards = "".join(f'''<div class="ind-tab"><img src="/app37/tools/showvehiclemodel/{cid}" alt="{name}圖片">
            <button onclick="window.location.assign('/app37/rentView/vehicleDetail/{cid}')">查看</button></div>'''
                            for cid, name in [("1", "輪椅"), ("20", "其他")])
            html = '<div class="col-md-9">' + cards + '</div>'
        elif path.endswith("/vehicleDetail/1"):
            html = variant_html("185")
        elif path.endswith("/vehicleDetail/20"):
            html = "<html>維護中</html>" if state["broken"] else variant_html("192", state["stock"], None, True)
        else:
            raise AssertionError("不應請求圖片、預約或其他來源")
        return httpx.Response(200, text=html)

    monkeypatch.setattr(borrow, "_snapshot", None)
    monkeypatch.setattr(borrow, "_snapshot_at", 0)
    monkeypatch.setattr(borrow, "REQUEST_INTERVAL_SECONDS", 0)
    monkeypatch.setattr(borrow.httpx, "Client", lambda **kwargs: client_class(
        transport=httpx.MockTransport(respond), **kwargs))
    return requests, state


def test_catalog_and_stock_share_ids_and_single_snapshot(source):
    requests, _ = source
    catalog, stock = fetch_catalog(), fetch_stock()
    assert [c.id for c in catalog] == ["1", "20"]
    assert {v.id for c in catalog for v in c.variants} == {s.variant_id for s in stock} == {"185", "192"}
    assert [(s.stock, s.waiting) for s in stock] == [(0, 13), (3, 0)]
    assert len(requests) == 3  # 無額外圖片、預約或同次重複抓取。


def test_callers_cannot_modify_cached_data(source):
    fetch_catalog()[0].variants[0].name = "被呼叫者修改"
    fetch_stock()[0].stock = 99
    assert fetch_catalog()[0].variants[0].name == "輔具"
    assert fetch_stock()[0].stock == 0


def test_broken_category_does_not_publish_partial_stock(source, monkeypatch):
    _, state = source
    fetch_stock()
    original = borrow._snapshot
    monkeypatch.setattr(borrow, "_snapshot_at", float("-inf"))
    state["broken"] = True
    with pytest.raises(ValueError, match="沒有任何款式"):
        fetch_stock()
    assert borrow._snapshot is original


def test_unreadable_count_is_not_reported_as_zero(source):
    _, state = source
    state["stock"] = "未知"
    with pytest.raises(ValueError, match="數值不完整"):
        fetch_stock()
    assert borrow._snapshot is None


@pytest.mark.parametrize("text", ["剩餘:-", "剩餘:無", "剩餘:"])
def test_explicit_empty_count_follows_readme(text):
    assert borrow.labelled_count(text, "剩餘") == 0
    assert borrow.labelled_count("欄位消失", "剩餘") is None


def test_center_coordinates_districts_and_lunch_break():
    centers = fetch_centers()
    assert {c.id for c in centers} == {"heyi", "south", "west"}
    assert {d for c in centers for d in c.districts} == {
        "中山區", "大同區", "士林區", "北投區", "內湖區", "信義區", "文山區", "南港區",
        "中正區", "萬華區", "大安區", "松山區"}
    assert all(25 < c.lat < 25.2 and 121.4 < c.lng < 121.7 for c in centers)
    assert all([(h.from_, h.to) for h in c.hours] == [("09:00", "12:00"), ("13:30", "17:00")] for c in centers)
    centers[0].districts.clear()
    assert len(fetch_centers()[0].districts) == 4


def test_calendar_keeps_saturday_open_and_applies_explicit_closures(monkeypatch):
    monkeypatch.setattr(cal, "_load_holidays", lambda year: {date(2026, 11, 10): "測試國定假日"})
    monkeypatch.setattr(cal, "_load_closures", lambda: {("heyi", date(2026, 11, 11)): "臨時休館"})
    days = fetch_center_calendar("heyi", date(2026, 11, 7), 6)
    assert [d.open for d in days] == [True, False, False, False, False, True]
    assert len(days[0].hours) == 2
    assert days[3].reason == "測試國定假日" and days[4].reason == "臨時休館"
    assert all(d.date == date(2026, 11, 7) + timedelta(days=i) for i, d in enumerate(days))
    assert all(not d.hours for d in days if not d.open)


def test_roc_closure_range_does_not_include_reopening_date():
    html = '''<div class="col-md-9">
    <p>南區輔具中心：115/10/9(五)休館，將於115/10/12(一)開館服務</p>
    <p>合宜、西區輔具中心：115/10/9(五)~115/10/12(一)休館，將於115/10/13(二)開館服務</p>
    </div>'''.encode()
    closures = cal.parse_closure_notice(html)
    assert len(closures) == 9
    assert ("south", date(2026, 10, 12)) not in closures
    assert ("heyi", date(2026, 10, 12)) in closures
    assert ("heyi", date(2026, 10, 13)) not in closures
    alternate = '<div class="col-md-9"><p>合宜中心115/10/9休館，115/10/12恢復服務</p></div>'.encode()
    assert set(cal.parse_closure_notice(alternate)) == {("heyi", date(2026, 10, 9))}


def test_unreadable_closure_requires_review():
    with pytest.raises(ValueError, match="人工確認"):
        cal.parse_closure_notice('<div class="col-md-9"><p>本中心休館，日期請看圖片</p></div>'.encode())


def test_government_weekends_do_not_override_center_weekdays():
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["西元日期", "是否放假", "備註"])
    for i in range(365):
        day = date(2026, 1, 1) + timedelta(days=i)
        note = "國定假日" if day == date(2026, 1, 1) else ""
        writer.writerow([day.strftime("%Y%m%d"), "2" if note or day.isoweekday() >= 6 else "0", note])
    holidays = cal.parse_holidays(buffer.getvalue().encode("utf-8-sig"), 2026)
    assert holidays == {date(2026, 1, 1): "國定假日"}


def test_missing_calendar_year_is_not_guessed():
    with pytest.raises(NotImplementedError, match="2027"):
        cal._load_holidays(2027)
