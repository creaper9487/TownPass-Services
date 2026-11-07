import json
import time
from datetime import date, timedelta

from app.config import get_settings
from app.features.catalog import service as catalog_service
from app.features.centers import service as centers_service
from app.tools.crawlers.schemas import CalendarDay
from app.tools.security import sign
from app.tools.timeutil import today

P = "/assistive/v1"


def signed_post(client, path, payload):
    body = json.dumps(payload).encode()
    ts = str(int(time.time()))
    headers = {"X-Timestamp": ts, "X-Signature": sign(get_settings().hook_secret, ts, body),
               "Content-Type": "application/json"}
    return client.post(P + path, content=body, headers=headers)


def new_mailbox(client):
    mb = client.post(f"{P}/mailboxes").json()
    return mb["mailbox_id"], {"Authorization": f"Bearer {mb['mailbox_key']}"}


def fake_calendar(center_id, start, days):
    return [CalendarDay(date=start + timedelta(days=i), open=True, hours=[{"from": "08:30", "to": "17:30"}])
            for i in range(days)]


CONTACT = {"name": "王小明", "mobile": "0912345678", "gender": "M"}


def borrow_body(mailbox_id, variant="101"):
    return {"service": "borrow", "mailbox_id": mailbox_id, "center_id": "heyi", "items": [variant], "contact": CONTACT}


def test_health(client):
    assert client.get(f"{P}/health").json() == {"status": "ok"}


def test_crawler_not_implemented_returns_501(client, monkeypatch):
    def not_implemented():
        raise NotImplementedError("測試尚未提供的爬蟲")

    monkeypatch.setattr(catalog_service, "fetch_catalog", not_implemented)
    res = client.get(f"{P}/catalog")
    assert res.status_code == 501
    assert res.json()["code"] == "NOT_IMPLEMENTED"


def test_catalog_etag(client, monkeypatch):
    monkeypatch.setattr(catalog_service, "fetch_catalog", lambda: [
        {"id": "1", "name": "輪椅類", "variants": [
            {"id": "101", "name": "一般型輪椅", "specs": ["座寬 18 吋"], "attrs": {"seat_width_in": 18}}]}])
    res = client.get(f"{P}/catalog")
    assert res.status_code == 200
    v = res.json()["categories"][0]["variants"][0]
    assert v["id"] == "101" and v["specs"] == ["座寬 18 吋"] and v["attrs"]["seat_width_in"] == 18
    res2 = client.get(f"{P}/catalog", headers={"If-None-Match": res.headers["etag"]})
    assert res2.status_code == 304


def test_stock_hook_and_since(client):
    assert signed_post(client, "/hooks/center/stock",
                       {"event_id": "e1", "variant_id": "101", "stock": 2, "waiting": 0}).status_code == 204
    snap = client.get(f"{P}/stock").json()
    assert snap["items"]["101"] == {"stock": 2, "waiting": 0}
    assert client.get(f"{P}/stock?since={snap['version']}").status_code == 304
    assert client.get(f"{P}/stock?since=0").json()["items"]["101"]["stock"] == 2
    # 簽章錯誤
    res = client.post(f"{P}/hooks/center/stock", json={"event_id": "e2", "variant_id": "1", "stock": 1, "waiting": 0})
    assert res.status_code == 401


def test_borrow_flow(client, monkeypatch):
    monkeypatch.setattr(centers_service, "fetch_center_calendar", fake_calendar)
    signed_post(client, "/hooks/center/stock", {"event_id": "e1", "variant_id": "101", "stock": 1, "waiting": 0})
    mailbox_id, auth = new_mailbox(client)

    # 缺 Idempotency-Key
    assert client.post(f"{P}/reservations", json=borrow_body(mailbox_id)).status_code == 422

    res = client.post(f"{P}/reservations", json=borrow_body(mailbox_id), headers={"Idempotency-Key": "k1"})
    assert res.status_code == 201, res.text
    r = res.json()
    assert set(r) == {"id", "access_key", "status", "pickup"}
    assert r["status"] == "booked"
    assert r["pickup"]["deadline"] == (today() + timedelta(days=1)).isoformat()
    assert client.get(f"{P}/stock").json()["items"]["101"]["stock"] == 0

    # 同 key 同內容 → 同結果；同 key 不同內容 → 409
    again = client.post(f"{P}/reservations", json=borrow_body(mailbox_id), headers={"Idempotency-Key": "k1"})
    assert again.json()["id"] == r["id"]
    conflict = client.post(f"{P}/reservations", json=borrow_body(mailbox_id, "999"), headers={"Idempotency-Key": "k1"})
    assert conflict.json()["code"] == "IDEMPOTENCY_CONFLICT"

    # 沒庫存
    oos = client.post(f"{P}/reservations", json=borrow_body(mailbox_id), headers={"Idempotency-Key": "k2"})
    assert oos.status_code == 409 and oos.json()["code"] == "OUT_OF_STOCK"

    # 信箱有 booked 事件
    ev = client.get(f"{P}/mailboxes/{mailbox_id}/events?wait=0", headers=auth).json()
    assert [e["type"] for e in ev["events"]] == ["reservation.booked"]
    assert ev["next_cursor"] == ev["events"][-1]["cursor"]

    # batchGet + cancel（重複呼叫結果相同）
    got = client.post(f"{P}/reservations:batchGet",
                      json=[{"id": r["id"], "access_key": r["access_key"]},
                            {"id": r["id"], "access_key": "wrong"}]).json()
    assert got[0]["status"] == "booked" and got[0]["version"] == 1
    assert got[1] == {"id": r["id"], "error": "BAD_KEY"}
    for _ in range(2):
        c = client.post(f"{P}/reservations/{r['id']}:cancel", json={"access_key": r["access_key"]})
        assert c.json() == {"id": r["id"], "status": "cancelled", "version": 2}
    bad = client.post(f"{P}/reservations/{r['id']}:cancel", json={"access_key": "wrong"})
    assert bad.status_code == 401 and bad.json()["code"] == "BAD_KEY"
    assert client.get(f"{P}/stock").json()["items"]["101"]["stock"] == 1


def test_calendar_and_borrow_api_work_when_closure_announcements_fail(client, monkeypatch):
    from app.features.reservation import service as reservation_service
    from app.tools.crawlers import _calendar_source as cal

    def unavailable():
        raise RuntimeError("官網公告暫時不可用")

    monkeypatch.setattr(cal, "_closures", None)
    monkeypatch.setattr(cal, "_closures_at", 0)
    monkeypatch.setattr(cal, "_fetch_closures", unavailable)
    monkeypatch.setattr(cal, "_load_holidays", lambda year: {})
    monkeypatch.setattr(reservation_service, "today", lambda: date(2026, 11, 10))
    response = client.get(f"{P}/centers/heyi/calendar?from=2026-11-10&days=14")
    assert response.status_code == 200, response.text
    assert len(response.json()["days"]) == 14
    assert signed_post(client, "/hooks/center/stock",
                       {"event_id": "fallback-stock", "variant_id": "101", "stock": 1, "waiting": 0}).status_code == 204
    mailbox_id, _ = new_mailbox(client)
    response = client.post(f"{P}/reservations", json=borrow_body(mailbox_id),
                           headers={"Idempotency-Key": "closure-fallback"})
    assert response.status_code == 201, response.text
    assert response.json()["status"] == "booked"
    assert response.json()["pickup"]["deadline"] == "2026-11-11"


def test_subscription_arrival(client, monkeypatch):
    # 分類對照使用固定 fixture，測試不連官方網站。
    monkeypatch.setattr(catalog_service, "fetch_catalog", lambda: [
        {"id": "1", "name": "輪椅", "variants": [{"id": "101", "name": "測試輪椅"}]}])
    signed_post(client, "/hooks/center/stock", {"event_id": "e1", "variant_id": "101", "stock": 0, "waiting": 5})
    mailbox_id, auth = new_mailbox(client)
    body = {"mailbox_id": mailbox_id, "variant_id": "101"}
    assert client.post(f"{P}/subscriptions", json=body, headers=auth).status_code == 201
    dup = client.post(f"{P}/subscriptions", json=body, headers=auth)
    assert dup.json()["code"] == "DUPLICATE_WAITLIST"
    assert client.post(f"{P}/subscriptions", json=body).json()["code"] == "BAD_KEY"

    signed_post(client, "/hooks/center/stock", {"event_id": "e2", "variant_id": "101", "stock": 1, "waiting": 4})
    ev = client.get(f"{P}/mailboxes/{mailbox_id}/events?wait=0", headers=auth).json()
    assert ev["events"][0]["type"] == "stock.arrived"


def test_offline_calendar_and_year_end_borrow_use_bundled_holidays(client, monkeypatch):
    import httpx
    from app.features.reservation import service as reservation_service
    from app.tools.crawlers import _calendar_source as cal

    requested_hosts = []
    client_class = httpx.Client

    def offline(request):
        requested_hosts.append(request.url.host)
        raise httpx.ConnectError("網路不可用", request=request)

    cal._load_holidays.cache_clear()
    monkeypatch.setattr(cal, "_closures", None)
    monkeypatch.setattr(cal, "_closures_at", 0)
    monkeypatch.setattr(cal, "_notice_closures", {})
    monkeypatch.setattr(cal.httpx, "Client", lambda **kwargs: client_class(
        transport=httpx.MockTransport(offline), **kwargs))
    monkeypatch.setattr(reservation_service, "today", lambda: date(2026, 12, 31))
    response = client.get(f"{P}/centers/heyi/calendar?from=2026-12-19&days=14")
    assert response.status_code == 200, response.text
    days = response.json()["days"]
    assert len(days) == 14
    assert days[-1]["date"] == "2027-01-01" and not days[-1]["open"]
    assert days[-1]["reason"] == "開國紀念日"
    assert signed_post(client, "/hooks/center/stock",
                       {"event_id": "offline-stock", "variant_id": "101", "stock": 1, "waiting": 0}).status_code == 204
    mailbox_id, _ = new_mailbox(client)
    response = client.post(f"{P}/reservations", json=borrow_body(mailbox_id),
                           headers={"Idempotency-Key": "offline-borrow"})
    assert response.status_code == 201, response.text
    assert response.json()["pickup"] == {"deadline": "2027-01-01", "open_dates": ["2026-12-31"]}
    # 公告失敗後回退，政府日曆完全沒有網路請求（借用時檢查品項存在也會打官網目錄，同一個主機）。
    assert set(requested_hosts) == {"tpap.gov.taipei"}
    cal._load_holidays.cache_clear()


def test_repair_status_hook(client):
    mailbox_id, auth = new_mailbox(client)
    body = {"service": "repair", "mailbox_id": mailbox_id, "items": ["輪椅"], "contact": CONTACT,
            "subject": {"name": "王小明", "id_no": "A123456789", "registered_district": "大安區",
                        "living_county": "臺北市", "living_district": "大安區"}}
    r = client.post(f"{P}/reservations", json=body, headers={"Idempotency-Key": "r1"}).json()
    assert r["status"] == "submitted" and r["pickup"] is None

    hook = {"event_id": "s1", "reservation_id": r["id"], "status": "confirmed", "occurred_at": "2026-11-07T10:00:00+08:00"}
    assert signed_post(client, "/hooks/center/status", hook).status_code == 204
    assert signed_post(client, "/hooks/center/status", hook).status_code == 204  # 去重
    ev = client.get(f"{P}/mailboxes/{mailbox_id}/events?wait=0", headers=auth).json()
    assert [e["type"] for e in ev["events"]] == ["reservation.confirmed"]

    # 只服務臺北市
    body["subject"]["living_county"] = "新北市"
    body["subject"]["living_district"] = "板橋區"
    res = client.post(f"{P}/reservations", json=body, headers={"Idempotency-Key": "r2"})
    assert res.status_code == 422 and res.json()["code"] == "NOT_ELIGIBLE"


def test_validation_does_not_echo_values(client):
    mailbox_id, _ = new_mailbox(client)
    body = borrow_body(mailbox_id)
    body["contact"] = {**CONTACT, "mobile": "SECRET-123"}
    res = client.post(f"{P}/reservations", json=body, headers={"Idempotency-Key": "v1"})
    assert res.status_code == 422
    assert res.json()["code"] == "INVALID_FIELD"
    assert "SECRET-123" not in res.text
    assert "contact.mobile" in res.json()["fields"]
